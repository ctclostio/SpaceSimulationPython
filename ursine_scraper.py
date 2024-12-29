import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote
import os
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import hashlib

class UrsinaScraper:
    def __init__(self):
        self.base_url = "https://www.ursinaengine.org"
        self.documentation_url = urljoin(self.base_url, "/documentation.html")
        self.api_reference_url = urljoin(self.base_url, "/api_reference.html")
        
        # Normalization / visited sets
        self.visited_urls = set()  # store only the "canonical" version of a URL (no #fragment)
        
        # Output
        self.output_dir = "ursina_docs"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Concurrency
        self.max_workers = 10
        self.request_delay = 0.3
        self.max_pages = 200
        self.session = requests.Session()  # re-use the same session for efficiency
        
        # Timing
        self.start_time = time.time()
        self.timeout = 1800  # 30 minute timeout

        # Thread-safety
        self.write_lock = threading.Lock()
        self.visit_lock = threading.Lock()

        # For BFS
        self.executor = None

        # Caching
        self.cache_dir = os.path.join(self.output_dir, ".cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache_timeout = 86400  # 24 hours cache validity

    def scrape_documentation(self):
        """
        Main method to scrape all documentation pages using a BFS-like approach
        and concurrent processing.
        """
        # Initialize a queue with our starting nodes
        to_visit = [
            (self.documentation_url, None),
            (self.api_reference_url, None)
        ]

        print(f"Starting BFS with roots: {self.documentation_url} and {self.api_reference_url}")
        with ThreadPoolExecutor(max_workers=self.max_workers) as self.executor:
            futures_map = {}

            while to_visit:
                # Stop if over time or page limit
                if (time.time() - self.start_time) > self.timeout:
                    print(f"Timeout of {self.timeout} seconds reached. Stopping.")
                    break
                
                if len(self.visited_urls) >= self.max_pages:
                    print(f"Max pages ({self.max_pages}) limit reached. Stopping.")
                    break

                # While we have items in `to_visit`, submit them
                next_url, next_title = to_visit.pop()
                
                # Normalize the URL so that #fragments do not cause re-scraping
                canonical_url = self._canonical_url(next_url)
                
                with self.visit_lock:
                    # Check again if we visited in the meantime
                    if canonical_url in self.visited_urls:
                        continue
                    self.visited_urls.add(canonical_url)

                # Submit a new scraping task
                future = self.executor.submit(self.process_url, next_url, next_title)
                futures_map[future] = canonical_url

                # Process futures that have completed to discover new links
                done_futures = []
                for fut in as_completed(futures_map, timeout=5.0):
                    done_futures.append(fut)
                
                # For each completed future, gather new links
                for fut in done_futures:
                    canonical_url_done = futures_map.pop(fut)
                    try:
                        result = fut.result()
                        if not result:
                            continue
                        # new_links is a list of (url, link_text)
                        new_links = result
                        for link, link_text in new_links:
                            # Avoid re-queueing duplicates
                            link_canonical = self._canonical_url(link)
                            with self.visit_lock:
                                if link_canonical not in self.visited_urls:
                                    to_visit.append((link, link_text))
                    except Exception as e:
                        print(f"Error processing {canonical_url_done}: {e}")

        # Ensure all outstanding tasks are completed
        self._drain_futures(futures_map)

        # Wrap up
        print("\nScraping completed!")
        print(f"Total pages scraped: {len(self.visited_urls)}")
        print(f"Documentation saved in '{self.output_dir}' directory.")

        # Close session
        self.session.close()

    def process_url(self, url, title):
        """
        Download the page, parse it, save the content, and return the new links found.
        """
        # Show progress
        with self.visit_lock:
            pages_scraped_so_far = len(self.visited_urls)
        print(f"[Scraping] {url} - Page {pages_scraped_so_far} of up to {self.max_pages}")

        time.sleep(self.request_delay)

        # Check cache first
        cache_key = self._get_cache_key(url)
        cache_file = os.path.join(self.cache_dir, cache_key)
        if os.path.exists(cache_file):
            cache_time = os.path.getmtime(cache_file)
            if (time.time() - cache_time) < self.cache_timeout:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return eval(f.read())

        # Actually fetch content
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = self.session.get(
                self._canonical_url(url),
                timeout=10,
                headers=headers,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # For HTML content
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                print(f"Skipping non-HTML content at {url}: {content_type}")
                return []

            # Parse the content
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Find the main content container
            main_content = soup.find('div', style='max-width: 800px; margin: auto;')
            if not main_content:
                main_content = soup
            
            # Extract all sections
            sections = []
            current_section = None
            current_content = []
            
            for elem in main_content.find_all(['h1', 'h2', 'h3', 'p', 'pre', 'div', 'table']):
                text = elem.get_text(strip=True)
                
                # Start of new section
                if elem.name in ['h1', 'h2', 'h3']:
                    if current_section and current_content:
                        sections.append((current_section, current_content))
                    
                    current_section = text
                    current_content = []
                    continue
                
                # Add content to current section
                if current_section:
                    if elem.name == 'table':
                        current_content.append(self._table_to_markdown(elem))
                    elif elem.name == 'pre':
                        code = elem.get_text(strip=True)
                        current_content.append(f"\n```python\n{code}\n```\n")
                    else:
                        content = self._convert_to_markdown(elem)
                        if content.strip():
                            current_content.append(content)
            
            # Save the last section
            if current_section and current_content:
                sections.append((current_section, current_content))
            
            # Save all sections
            for section_text, content in sections:
                local_filename = os.path.join(self.output_dir, f"api_{section_text.lower().replace(' ', '_')}.txt")
                file_content = [
                    "---",
                    f"title: API Reference - {section_text}",
                    f"url: {url}#{section_text.replace(' ', '_')}",
                    f"scraped_at: {time.ctime()}",
                    "---\n",
                    f"# {section_text}\n"
                ] + content
                
                with self.write_lock:
                    with open(local_filename, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(filter(None, file_content)))
                print(f"Saved API documentation for {section_text}")
            
            # Continue with link extraction
            return self.extract_links(soup, url)
                
        except requests.RequestException as exc:
            print(f"Error fetching {url}: {exc}")
            return []
        except Exception as e:
            print(f"Unexpected error processing {url}: {e}")
            return []

    def _generate_markdown_content(self, soup, url):
        """
        Generate comprehensive Markdown content with improved content extraction.
        """
        content = []
        
        # Add metadata
        content.append(f"---")
        content.append(f"title: {soup.title.string if soup.title else 'Untitled'}")
        content.append(f"url: {url}")
        content.append(f"scraped_at: {time.ctime()}")
        content.append(f"---\n\n")

        # Find the main content
        main_content = None
        
        # Try to find the main content container with different selectors
        selectors = [
            {'style': 'font-size: 20.0px;max-width: 1200px; margin: auto;'},
            {'class_': 'content'},
            {'id': 'content'},
            {'class_': 'documentation-content'},
            {'style': 'max-width: 800px; margin: auto;'},  # API reference style
            {'class_': 'api-content'}
        ]
        
        for selector in selectors:
            main_content = soup.find('div', **selector)
            if main_content:
                break
        
        if not main_content:
            # If no specific container found, look for the largest text block
            text_blocks = soup.find_all(['div', 'article', 'main'])
            if text_blocks:
                main_content = max(text_blocks, key=lambda x: len(x.get_text()))
        
        if main_content:
            # Remove navigation and footer if present
            for nav in main_content.find_all(['nav', 'footer']):
                nav.decompose()
            
            # Convert the content to markdown
            content.append(self._convert_to_markdown(main_content))
        else:
            # Fallback to the entire document body
            body = soup.find('body')
            if body:
                content.append(self._convert_to_markdown(body))
            else:
                content.append(self._convert_to_markdown(soup))

        return "\n".join(content)

    def _convert_to_markdown(self, soup_element):
        """
        Enhanced HTML to Markdown conversion with better handling of documentation elements.
        """
        markdown = []
        
        # Handle both single elements and lists of elements
        elements = [soup_element] if not isinstance(soup_element, list) else soup_element
        
        for elem in elements:
            if elem is None:
                continue
                
            # Handle text nodes
            if elem.name is None:
                text = elem.string.strip() if elem.string else ''
                if text:
                    markdown.append(text)
                continue
                    
            # HEADINGS
            if elem.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = int(elem.name[1])
                text = elem.get_text(strip=True)
                markdown.append(f"{'#' * level} {text}\n")
            
            # SPECIAL URSA DOCS AND API CONTENT
            if elem.name == 'div':
                if 'style' in elem.attrs:
                    if 'font-size: 20.0px' in elem.attrs['style'] or 'max-width: 800px' in elem.attrs['style']:
                        # Process all children except the first title div for docs
                        # or process all children for API reference
                        children = list(elem.children)
                        if len(children) > 1:
                            markdown.append(self._convert_to_markdown(children[1:]))
                        continue
                elif 'class' in elem.attrs and 'api-content' in elem.attrs['class']:
                    # Handle API reference content
                    markdown.append(self._convert_to_markdown(list(elem.children)))
                    continue

            # PARAGRAPHS
            elif elem.name == 'p':
                text = elem.get_text(strip=True)
                if text:
                    markdown.append(text + "\n")

            # CODE BLOCKS
            elif elem.name == 'div' and 'code_block' in elem.get('class', []):
                code = elem.get_text(strip=True)
                # Remove 'copy' text if present at the start
                code = re.sub(r'^copy\s*from\s*', '', code)
                code = re.sub(r'^copy\s*', '', code)
                # Fix Python code formatting
                code = self._format_python_code(code)
                # Add extra newline for better readability
                markdown.append(f"\n```python\n{code}\n```\n")
            elif elem.name == 'pre':
                code = elem.get_text()
                # Remove 'copy' text if present at the start
                code = re.sub(r'^copy\s*from\s*', '', code)
                code = re.sub(r'^copy\s*', '', code)
                language = self._detect_code_language(elem)
                if language == 'python':
                    code = self._format_python_code(code)
                # Add extra newline for better readability
                markdown.append(f"\n```{language}\n{code}\n```\n")

            # LISTS
            elif elem.name == 'ul':
                markdown.append(self._list_to_markdown(elem, ordered=False))
            elif elem.name == 'ol':
                markdown.append(self._list_to_markdown(elem, ordered=True))

            # TABLES
            elif elem.name == 'table':
                markdown.append(self._table_to_markdown(elem) + "\n")

            # IMAGES
            elif elem.name == 'img':
                src = elem.get('src', '')
                alt = elem.get('alt', '')
                if src:
                    markdown.append(f"![{alt}]({src})\n")

            # LINKS
            elif elem.name == 'a':
                href = elem.get('href', '')
                text = elem.get_text(strip=True)
                if href:
                    markdown.append(f"[{text}]({href})")
                else:
                    markdown.append(text)

            # BLOCKQUOTES
            elif elem.name == 'blockquote':
                quote = elem.get_text(strip=True)
                markdown.append(f"> {quote}\n")

            # HORIZONTAL RULES
            elif elem.name == 'hr':
                markdown.append("---\n")

            # CONTENT CONTAINERS
            elif elem.name in ['div', 'span', 'section', 'article']:
                # Handle special Ursina documentation containers
                if 'style' in elem.attrs and 'font-size: 20.0px' in elem.attrs['style']:
                    # Process all children except the first title div
                    children = list(elem.children)
                    if len(children) > 1:
                        markdown.append(self._convert_to_markdown(children[1:]))
                else:
                    # Process children recursively
                    for child in elem.children:
                        if hasattr(child, 'name'):
                            markdown.append(self._convert_to_markdown(child))
                        elif isinstance(child, str) and child.strip():
                            markdown.append(child.strip() + " ")

        return "\n".join(markdown)

    def _format_python_code(self, code):
        """
        Format Python code with minimal changes to preserve readability.
        """
        # First, preserve original line breaks and indentation
        lines = code.replace('\r\n', '\n').split('\n')
        formatted_lines = []
        
        for line in lines:
            # Skip empty lines
            if not line.strip():
                formatted_lines.append('')
                continue
            
            # Get original indentation
            indent = len(line) - len(line.lstrip())
            processed = line.lstrip()
            
            # Remove 'copy' text if at start of line
            processed = re.sub(r'^copy\s*from\s*', '', processed)
            processed = re.sub(r'^copy\s*', '', processed)
            
            # Fix spacing around keywords
            keywords = ['def', 'if', 'for', 'in', 'while', 'class', 'return', 'else', 'elif', 'import', 'from']
            for keyword in keywords:
                processed = re.sub(fr'\b{keyword}(\w)', fr'{keyword} \1', processed)
            
            # Fix spacing around operators without breaking words
            processed = re.sub(r'([^=!<>])=([^=\s])', r'\1 = \2', processed)  # Assignment
            processed = re.sub(r'([=!<>])=([^=\s])', r'\1= \2', processed)    # Comparison
            processed = re.sub(r'([^=\s])=([=])', r'\1 =\2', processed)       # Comparison
            processed = re.sub(r'\+\s*=', ' += ', processed)                  # Plus equals
            processed = re.sub(r'-\s*=', ' -= ', processed)                   # Minus equals
            processed = re.sub(r'\*\s*=', ' *= ', processed)                 # Times equals
            processed = re.sub(r'/\s*=', ' /= ', processed)                  # Divide equals
            
            # Fix spacing around commas without breaking words
            processed = re.sub(r'([^,\s]),([^,\s])', r'\1, \2', processed)
            
            # Add back original indentation
            formatted_lines.append(' ' * indent + processed)
        
        return '\n'.join(formatted_lines)

    def _detect_code_language(self, element):
        """
        Detect code language from class names, parent elements, or content heuristics.
        """
        # Check class names
        classes = element.get('class', [])
        for cls in classes:
            if cls.startswith('language-'):
                return cls[len('language-'):]
            
        # Check parent elements
        parent = element.parent
        if parent and parent.get('class'):
            for cls in parent.get('class'):
                if cls.startswith('language-'):
                    return cls[len('language-'):]

        # Content-based heuristics
        code = element.get_text()
        if re.search(r'def\s+\w+\s*\(.*\):|class\s+\w+[:\(]', code):
            return 'python'
        elif re.search(r'function\s+\w+\s*\(.*\)|const\s+\w+\s*=|let\s+\w+\s*=|var\s+\w+\s*=', code):
            return 'javascript'
        elif re.search(r'<\w+>.*</\w+>|<\w+\s+.*?/?>', code):
            return 'html'
        
        return ''

    def _list_to_markdown(self, list_element, ordered=False, indent_level=0):
        """
        Convert HTML list to Markdown with proper indentation and nested list support.
        """
        markdown = []
        indent = "    " * indent_level
        
        for i, li in enumerate(list_element.find_all('li', recursive=False), start=1):
            # Handle the list item's own text first
            text_content = []
            for child in li.children:
                if isinstance(child, str):
                    text = child.strip()
                    if text:
                        text_content.append(text)
                elif child.name not in ['ul', 'ol']:
                    text = child.get_text(strip=True)
                    if text:
                        text_content.append(text)
            
            prefix = f"{i}. " if ordered else "- "
            markdown.append(indent + prefix + " ".join(text_content))
            
            # Handle nested lists
            nested_lists = li.find_all(['ul', 'ol'], recursive=False)
            for nested in nested_lists:
                nested_md = self._list_to_markdown(
                    nested,
                    ordered=nested.name == 'ol',
                    indent_level=indent_level + 1
                )
                markdown.append(nested_md)
        
        return "\n".join(markdown)

    def _table_to_markdown(self, table):
        """
        Convert HTML table to Markdown with alignment and complex content support.
        """
        headers = []
        alignments = []
        rows = []

        # Process headers
        header_row = table.find('tr')
        if header_row:
            for th in header_row.find_all(['th', 'td']):
                headers.append(th.get_text(strip=True))
                # Determine alignment from style or class
                style = th.get('style', '')
                if 'text-align: right' in style:
                    alignments.append('---:')
                elif 'text-align: center' in style:
                    alignments.append(':---:')
                elif 'text-align: left' in style:
                    alignments.append(':---')
                else:
                    alignments.append('---')

        # Process rows
        for tr in table.find_all('tr')[1:] if headers else table.find_all('tr'):
            row = []
            for td in tr.find_all(['td', 'th']):
                cell_content = []
                for elem in td.children:
                    if isinstance(elem, str):
                        text = elem.strip()
                        if text:
                            cell_content.append(text)
                    else:
                        # Handle links and other elements
                        if elem.name == 'a':
                            href = elem.get('href', '')
                            text = elem.get_text(strip=True)
                            if href:
                                cell_content.append(f"[{text}]({href})")
                            else:
                                cell_content.append(text)
                        elif elem.name == 'code':
                            cell_content.append(f"`{elem.get_text(strip=True)}`")
                        else:
                            text = elem.get_text(strip=True)
                            if text:
                                cell_content.append(text)
                row.append(" ".join(cell_content))
            rows.append(row)

        if not headers and rows:
            headers = [""] * len(rows[0])
            alignments = ["---"] * len(rows[0])

        # Build table
        table_md = []
        if headers:
            table_md.append("| " + " | ".join(headers) + " |")
            table_md.append("| " + " | ".join(alignments) + " |")
        for row in rows:
            table_md.append("| " + " | ".join(row) + " |")

        return "\n".join(table_md)

    def _get_cache_key(self, url):
        """
        Generate a cache key from the URL.
        """
        return hashlib.md5(url.encode('utf-8')).hexdigest() + ".cache"

    def extract_links(self, soup, current_url):
        """
        Extract all relevant documentation and API reference links from the page,
        with special handling for API component fragments.
        """
        links = []
        
        # Special handling for API reference page
        if '/api_reference.html' in current_url:
            # Find all headings that might be API components
            for heading in soup.find_all(['h1', 'h2', 'h3']):
                component_name = heading.get_text(strip=True)
                if component_name and '(' in component_name:  # Likely an API component
                    # Create a link to this component
                    component_url = f"{self.base_url}/api_reference.html#{component_name.split('(')[0].strip()}"
                    links.append((component_url, component_name))
            
            # Also find explicit links to API components
            for a in soup.find_all('a', href=True):
                href = a['href'].strip()
                if href.startswith('#'):  # Fragment identifier
                    full_url = f"{self.base_url}/api_reference.html{href}"
                    links.append((full_url, a.get_text(strip=True)))
        else:
            # Standard link extraction for other pages
            for a in soup.find_all('a', href=True):
                href = a['href'].strip()
                full_url = urljoin(current_url, href)
                
                if href.startswith('/'):
                    full_url = urljoin(self.base_url, href)
                elif not href.startswith(('http://', 'https://')):
                    full_url = urljoin(self.base_url, '/' + href)
                
                if self.is_valid_url(full_url):
                    links.append((full_url, a.get_text(strip=True)))
        
        return links

    def is_valid_url(self, url):
        """
        Check if URL is valid and belongs to ursinaengine.org,
        focusing on API reference pages.
        """
        parsed = urlparse(url)
        if parsed.scheme not in ['http', 'https']:
            return False
        if parsed.netloc not in ['www.ursinaengine.org', 'ursinaengine.org']:
            return False
        # Skip assets
        if url.endswith(('.png', '.jpg', '.jpeg', '.gif', '.css', '.js')):
            return False
        # Focus on API reference pages and their fragments
        if '/api_reference.html' in url:
            return True
        return True

    def clean_filename(self, url, title=None):
        """
        Convert URL or title to a valid filename for local saving.
        """
        if title:
            # Clean the title to create a filename
            filename = re.sub(r'[^\w\s-]', '', title.lower())
            filename = re.sub(r'[-\s]+', '_', filename)
        else:
            # Use URL path if no title
            parsed = urlparse(url)
            path = unquote(parsed.path)
            if not path.strip('/'):
                filename = 'index'
            else:
                filename = path.strip('/')
                # remove trailing .html if present
                if filename.endswith('.html'):
                    filename = filename[:-5]
            filename = re.sub(r'[^\w\s-]', '_', filename)
        
        return os.path.join(self.output_dir, f"{filename}.txt")

    def _canonical_url(self, url):
        """
        Remove fragment (#some-section) from the URL to unify references,
        except when specifically scraping sections.
        """
        parsed = urlparse(url)
        # Preserve fragment if it's an API reference section
        if '/api_reference.html' in url and parsed.fragment:
            return url
        return parsed._replace(fragment='').geturl()

    def scrape_section(self, section_url):
        """
        Scrape a specific section from the API reference page.
        """
        # Normalize URL to include fragment
        parsed = urlparse(section_url)
        if not parsed.fragment:
            raise ValueError("Section URL must include a fragment identifier")
            
        # Fetch and parse the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = self.session.get(section_url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Find the specific section
        section_id = parsed.fragment
        section = soup.find(id=section_id)
        if not section:
            raise ValueError(f"Section with id '{section_id}' not found")
            
        # Extract section content
        content = []
        current = section
        while current:
            # Stop at next section
            if current.name in ['h1', 'h2', 'h3'] and current != section:
                break
                
            # Convert content to markdown
            if current.name == 'table':
                content.append(self._table_to_markdown(current))
            elif current.name == 'pre':
                code = current.get_text(strip=True)
                content.append(f"\n```python\n{code}\n```\n")
            else:
                md = self._convert_to_markdown(current)
                if md.strip():
                    content.append(md)
                    
            current = current.find_next_sibling()
            
        # Save the section
        filename = os.path.join(self.output_dir, f"api_{section_id}.txt")
        file_content = [
            "---",
            f"title: API Reference - {section_id.replace('_', ' ')}",
            f"url: {section_url}",
            f"scraped_at: {time.ctime()}",
            "---\n",
            f"# {section_id.replace('_', ' ')}\n"
        ] + content
        
        with self.write_lock:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(filter(None, file_content)))
                
        return filename

    def _drain_futures(self, futures_map):
        """
        Wait for any still-running tasks to finish before we exit.
        """
        if not futures_map:
            return
        print("Draining any remaining futures...")
        for fut in as_completed(futures_map):
            try:
                fut.result()
            except Exception as e:
                print(f"Error in future: {e}")
        futures_map.clear()


if __name__ == "__main__":
    scraper = UrsinaScraper()
    scraper.scrape_documentation()
