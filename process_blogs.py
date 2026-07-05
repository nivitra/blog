import os
import json
import re

def parse_inlines(text):
    # Escape HTML to prevent injection and rendering issues
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    # Render Bold: **text**
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
    # Render Italic: *text*
    text = re.sub(r"\*(.*?)\*", r"<em>\1</em>", text)
    # Render Links: [text](url)
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', text)
    
    return text

def md_to_html(md_text):
    lines = md_text.split("\n")
    html_lines = []
    in_list = False
    in_ol = False
    in_quote = False
    
    for line in lines:
        line_stripped = line.strip()
        
        # Close quote if it ends
        if in_quote and not line_stripped.startswith(">"):
            html_lines.append("</blockquote>")
            in_quote = False
            
        # Close bullet list if it ends
        if in_list and not (line_stripped.startswith("- ") or line_stripped.startswith("* ")):
            html_lines.append("</ul>")
            in_list = False
            
        # Close ordered list if it ends
        if in_ol and not re.match(r"^\d+\.\s", line_stripped):
            html_lines.append("</ol>")
            in_ol = False
            
        if not line_stripped:
            continue
            
        # Headings
        if line_stripped.startswith("### "):
            html_lines.append(f"<h3>{parse_inlines(line_stripped[4:])}</h3>")
        elif line_stripped.startswith("## "):
            html_lines.append(f"<h2>{parse_inlines(line_stripped[3:])}</h2>")
        elif line_stripped.startswith("# "):
            html_lines.append(f"<h1>{parse_inlines(line_stripped[2:])}</h1>")
        # Blockquotes
        elif line_stripped.startswith(">"):
            quote_content = line_stripped[1:].strip()
            if not in_quote:
                html_lines.append("<blockquote>")
                in_quote = True
            html_lines.append(f"<p>{parse_inlines(quote_content)}</p>")
        # Bullet list
        elif line_stripped.startswith("- ") or line_stripped.startswith("* "):
            item_content = line_stripped[2:]
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{parse_inlines(item_content)}</li>")
        # Ordered list
        elif re.match(r"^\d+\.\s", line_stripped):
            item_content = re.sub(r"^\d+\.\s", "", line_stripped)
            if not in_ol:
                html_lines.append("<ol>")
                in_ol = True
            html_lines.append(f"<li>{parse_inlines(item_content)}</li>")
        # Horizontal rule
        elif line_stripped == "---":
            html_lines.append("<hr>")
        # Paragraph
        else:
            html_lines.append(f"<p>{parse_inlines(line_stripped)}</p>")
            
    # Clean up unclosed tags
    if in_quote:
        html_lines.append("</blockquote>")
    if in_list:
        html_lines.append("</ul>")
    if in_ol:
        html_lines.append("</ol>")
        
    return "\n".join(html_lines)

def process_all_blogs():
    blog_dir = "speaksy_blogs_final"
    files = sorted([f for f in os.listdir(blog_dir) if f.endswith(".md")])
    
    print(f"Found {len(files)} markdown files in {blog_dir}")
    
    blogs = []
    title_seen = {} # map title -> index of first seen version
    
    for fn in files:
        # Extract ID from filename (e.g. 001 from 001-why...)
        file_id = fn.split("-", 1)[0]
        
        filepath = os.path.join(blog_dir, fn)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        parts = content.split("---", 2)
        if len(parts) < 3:
            print(f"Warning: {fn} does not have valid frontmatter")
            continue
            
        fm_text = parts[1]
        body_text = parts[2].strip()
        
        # Parse frontmatter
        fm = {}
        for line in fm_text.strip().split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip().strip("\"").strip("\u0027")
                
        # Clean title
        title = fm.get("title", "Untitled").strip()
        author = fm.get("author", "Unknown").strip()
        role = fm.get("role", "Co-founder").strip()
        date = fm.get("date", "2026-07-05").strip()
        category = fm.get("category", "general").strip()
        platform = fm.get("platform", "Speaksy Voice AI").strip()
        website = fm.get("website", "https://speaksy.in").strip()
        
        # Calculate approximate reading time (WPM = 200)
        word_count = len(body_text.split())
        read_time = max(1, round(word_count / 200))
        
        # Convert body to HTML
        html_body = md_to_html(body_text)
        
        # Determine uniqueness
        is_duplicate = False
        duplicate_of = None
        
        # Standardize title for matching (lowercase and stripped)
        title_key = title.lower().strip()
        if title_key in title_seen:
            is_duplicate = True
            duplicate_of = title_seen[title_key]
        else:
            title_seen[title_key] = file_id
            
        blog_obj = {
            "id": file_id,
            "filename": fn,
            "title": title,
            "author": author,
            "role": role,
            "date": date,
            "category": category,
            "platform": platform,
            "website": website,
            "read_time": read_time,
            "word_count": word_count,
            "is_duplicate": is_duplicate,
            "duplicate_of": duplicate_of,
            "body": html_body
        }
        blogs.append(blog_obj)
        
    # Write to blogs_data.js
    output_path = "blogs_data.js"
    with open(output_path, "w", encoding="utf-8") as out:
        out.write("// Speaksy Blog Database - Autogenerated by process_blogs.py\n")
        out.write("window.speaksyBlogs = ")
        json.dump(blogs, out, indent=2, ensure_ascii=False)
        out.write(";\n")
        
    print(f"Successfully processed {len(blogs)} blogs and saved to {output_path}")
    print(f"Unique articles: {len(title_seen)}")

if __name__ == "__main__":
    process_all_blogs()
