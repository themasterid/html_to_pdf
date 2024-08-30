import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# ! За суп респект :)
from bs4 import BeautifulSoup
from PyPDF2 import PdfMerger
from weasyprint import CSS, HTML

# Путь к локальной папке с сайтом
# ! У нас у всех есть этот путь, переделать!
# ! Старайся не использовать кириллицу в путях. 
base_path = (
    "/Users/pavelpetropavlov/Yandex.Disk.localized/литература/runestone-gh-pages/"
)

# ! Константы это будущее python!
# Путь к индексному файлу
index_path = os.path.join(base_path, "index.html")

# ! Константы это будущее python!
# Путь для сохранения конечного PDF-файла
output_path = "output_local.pdf"

# ! Ты оставляешь комментарии но делаешь ты это без уважения к функциям!
# ! Мы против типизации?
# Функция для получения всех внутренних ссылок
def get_internal_links(file_path):
    """Функция для получения всех внутренних ссылок."""
    # ! Док_стринги на веки!

    # ! Сделать свой контекстный менеджер, __enter__ и __exit__ еще никто не отменял
    with open(file_path, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")
    links = []
    for li in soup.find_all("li", class_="toctree-l1"):
        # ! Красивое название переменной, но ты можешь придумать лучше.
        # ! li туда же!
        a = li.find("a", class_="reference internal")
        if a:
            links.append(a["href"])
    return links


# Функция для удаления <footer> и <div id="navbar"> из HTML-документа
def remove_unwanted_elements(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    footer = soup.find("footer")
    if footer:
        footer.decompose()

    noscripts = soup.find_all("noscript")
    for noscript in noscripts:
        noscript.decompose()

    scripts = soup.find_all("script")
    for script in scripts:
        script.decompose()

    navbar = soup.find("div", id="navbar")
    if navbar:
        navbar.decompose()

    for rel_id in ("relations-next", "relations-prev"):
        relations_next = soup.find("li", id=rel_id)
        if relations_next:
            relations_next.decompose()

    javascript_warning = soup.find(
        lambda tag: tag.name == "div" and "Please enable JavaScript" in tag.text
    )
    if javascript_warning:
        javascript_warning.parent.decompose()

    headerlinks = soup.find_all("a", class_="headerlink")
    for headerlink in headerlinks:
        headerlink.decompose()

    div_classess = ("video_popup", "admonition- admonition", "ac_actions")
    for div_class in div_classess:
        ac_sections = soup.find_all("div", class_=div_class)
        for ac_section in ac_sections:
            ac_section.decompose()

    id_navs = ("navLinkBgLeft", "navLinkBgRight")
    for id_nav in id_navs:
        navLinkBgRight = soup.find("a", id=id_nav)
        if navLinkBgRight:
            navLinkBgRight.decompose()

    return str(soup)


# Функция для создания PDF из HTML-файла
def create_pdf(html_file):
    with open(html_file, "r") as file:
        html_content = file.read()
    modified_html_content = remove_unwanted_elements(html_content)

    # Увы тут нельзя вызвать еще и HTML() т.к. происходит segmantation fault
    return modified_html_content


# Получение всех внутренних ссылок
internal_links = get_internal_links(index_path)

# Список всех HTML-файлов для конвертации
html_files = [index_path] + [os.path.join(base_path, link) for link in internal_links]

# Создание временных PDF-файлов
temp_pdf_files = []
with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
    futures = {
        executor.submit(create_pdf, html_file): i
        for i, html_file in enumerate(html_files)
    }
    for future in as_completed(futures):
        index = futures[future]
        temp_pdf_path = f"{index}.pdf"
        temp_pdf_files.append(temp_pdf_path)

        modified_html_content = future.result()
        HTML(string=modified_html_content, base_url=f"file://{base_path}").write_pdf(
            temp_pdf_path,
            stylesheets=[
                CSS(url=f"file://{base_path}_static/pygments.css"),
                CSS(url=f"file://{base_path}_static/basic.css"),
            ],
        )

# Объединение всех временных PDF-файлов в один
merger = PdfMerger()
for temp_pdf_file in sorted(temp_pdf_files, key=lambda elem: int(elem.split(".")[0])):
    merger.append(temp_pdf_file)

merger.write(output_path)
merger.close()

# Удаление временных PDF-файлов
for temp_pdf_file in temp_pdf_files:
    os.remove(temp_pdf_file)

print(f"PDF успешно создан и сохранен как {output_path}")
