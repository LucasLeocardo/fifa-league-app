"""
Le a tela de "Desempenho individual" (EA FC / FIFA) com EasyOCR e gera um CSV
com POS, Name, NF, G e AST.

Como funciona:
    1. EasyOCR devolve, para cada texto, a caixa (4 pontos), o texto e a confianca.
    2. As COLUNAS sao ancoradas no proprio cabecalho (POS/Nome/NF/G/AST), que o
       EasyOCR le muito bem -> independe da resolucao da foto.
    3. As LINHAS sao ancoradas na coluna Nome (1 grupo por jogador) e cada token
       e atribuido ao nome mais proximo em Y e a coluna mais proxima em X.
    4. G e AST sao lidos numa SEGUNDA passada, recortando a celula de cada linha
       e rodando o OCR so com digitos. A leitura global do EasyOCR costuma pular
       digitos isolados (0/1) -> a coluna AST inteira sumia. O recorte resolve.
"""

import os
import re
import csv
import io
import cv2
import easyocr

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "ratings.csv")

# Palavras de cabecalho/rodape que NAO sao jogadores (PT e EN).
NOT_A_PLAYER = {"NOME", "NAME", "POS", "POSA", "NF", "AST", "NOTA", "DESEMPENHO",
                "PERFORMANCE", "VOLTAR", "BACK", "ORDENAR", "SORT", "ROLAGEM",
                "SCROLL", "MARC", "GER", "GUIU"}

_reader = None


def get_reader(languages=("pt", "en")):
    """Cria (uma vez) o leitor do EasyOCR. Cai para so 'pt' se a combinacao falhar."""
    global _reader
    if _reader is None:
        try:
            _reader = easyocr.Reader(list(languages))
        except Exception:
            _reader = easyocr.Reader(["pt"])
    return _reader


def read_image(path):
    """Roda o EasyOCR e devolve tokens {text, conf, x, y, w, h, cx, cy}."""
    result = get_reader().readtext(path)
    items = []
    for bbox, text, conf in result:
        xs = [float(p[0]) for p in bbox]
        ys = [float(p[1]) for p in bbox]
        x1, x2, y1, y2 = min(xs), max(xs), min(ys), max(ys)
        items.append({
            "text": text.strip(), "conf": float(conf),
            "x": x1, "y": y1, "w": x2 - x1, "h": y2 - y1,
            "cx": (x1 + x2) / 2, "cy": (y1 + y2) / 2,
        })
    return items


def _letters_only(text):
    return re.sub(r"[^A-Za-z]", "", text).upper()


def normalize_rating(text):
    """'6,5'/'6.5' -> 6.5 | 'ND'/'N/A'/'NA'/'-' -> 'ND' | senao None."""
    t = text.upper().replace(" ", "")
    m = re.search(r"(\d)\s*[.,]\s*(\d)", t)      # nota tipo 6,5 (prioridade)
    if m:
        return float(f"{m.group(1)}.{m.group(2)}")
    # Marcadores de "sem nota": ND (PT), N/A ou NA (EN), tracos.
    alnum = re.sub(r"[^A-Z0-9]", "", t)
    if t in {"-", "--"} or (alnum.startswith("N") and not re.search(r"\d", alnum)):
        return "ND"
    m = re.search(r"\d", t)                       # nota inteira (raro)
    if m:
        return float(m.group(0))
    return None


def normalize_count(text):
    """Texto da celula G/AST -> inteiro (vazio vira 0)."""
    digits = re.sub(r"[^0-9]", "", text)
    return int(digits) if digits else 0


def ocr_digit_cell(img, cx, cy, half_w, half_h, min_conf=0.5):
    """Recorta a celula (cx,cy) e le SO digitos. Devolve int ou None se vazia.

    A leitura global do EasyOCR pula digitos isolados (o '0'/'1' da coluna AST
    some). Recortando a celula, deixando em cinza, ampliando e realcando o
    contraste, o reconhecimento fica confiavel mesmo em fotos escuras/pequenas.
    Leituras abaixo de `min_conf` sao descartadas (evita falso positivo tipo o
    '4' com conf 0.04 quando a celula so tem um '0').
    """
    if img is None:
        return None
    height, width = img.shape[:2]
    x1, x2 = max(0, int(cx - half_w)), min(width, int(cx + half_w))
    y1, y2 = max(0, int(cy - half_h)), min(height, int(cy + half_h))
    if x2 - x1 < 3 or y2 - y1 < 3:
        return None
    crop = img[y1:y2, x1:x2]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=6, fy=6, interpolation=cv2.INTER_CUBIC)
    gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    result = get_reader().readtext(gray, allowlist="0123456789", detail=1)
    best = None
    for _, text, conf in result:
        digits = re.sub(r"[^0-9]", "", text)
        if digits and conf >= min_conf and (best is None or conf > best[1]):
            best = (int(digits), conf)
    return best[0] if best else None


def clean_name(text):
    """Tira simbolos soltos no comeco e poe espaco apos a inicial."""
    name = text.strip(" .-_|").strip()
    name = re.sub(r"^[^A-Za-zÀ-ÿ]+", "", name)          # lixo no inicio
    name = re.sub(r"\.([A-Za-zÀ-ÿ])", r". \1", name)    # "F.Dimarco" -> "F. Dimarco"
    return re.sub(r"\s+", " ", name).strip()


def _column_center(items, labels, cy=None, tol=None, x_min=None, x_max=None):
    """Acha o token de cabecalho cujo texto casa com um rotulo.

    Se cy/tol forem dados, so considera tokens na linha do cabecalho -> deixa
    seguro casar rotulos de uma letra so (ex.: 'G', 'A') sem pegar dados.
    x_min/x_max limitam a busca em X -> evita casar 'Goals'/'Assists' de um
    painel lateral (telas de PC) com as colunas G/AST da tabela.
    """
    candidates = [it for it in items if _letters_only(it["text"]) in labels]
    if cy is not None:
        candidates = [it for it in candidates if abs(it["cy"] - cy) <= tol]
    if x_min is not None:
        candidates = [it for it in candidates if it["cx"] >= x_min]
    if x_max is not None:
        candidates = [it for it in candidates if it["cx"] <= x_max]
    if not candidates:
        return None
    return max(candidates, key=lambda it: it["conf"])  # o mais confiavel


def extract(items, img=None):
    """Estrutura os tokens do EasyOCR em linhas de jogador (PT ou EN).

    `img` (BGR do cv2) e opcional: quando dado, G/AST sao lidos por recorte de
    celula (2a passada), o que captura os digitos isolados que a leitura global
    do EasyOCR costuma pular.
    """
    # 'Nome'/'Name' e o cabecalho mais confiavel em qualquer idioma -> ancora.
    h_name = _column_center(items, {"NOME", "NAME"})
    if not h_name:
        raise RuntimeError("Nao achei o cabecalho 'Nome/Name' na imagem.")
    name_cx, header_cy = h_name["cx"], h_name["cy"]
    band = 0.9 * h_name["h"]                       # so a linha do cabecalho

    # Rotulos de cabecalho em PT e EN.
    #   Posicao: PT 'POS'  | EN 'POS'
    #   Nome:    PT 'Nome' | EN 'Name'
    #   Nota:    PT 'NF'   | EN 'RR'
    #   Gols:    PT 'G'    | EN 'G'
    #   Assist.: PT 'AST'  | EN 'AST'
    h_pos = _column_center(items, {"POS", "POSA", "POSITION"}, header_cy, band)
    h_nf = _column_center(items, {"NF", "RR", "NOTA", "RATING", "RAT", "MR"},
                          header_cy, band)

    # Tokens de dados = abaixo do cabecalho.
    data = [it for it in items if it["cy"] > header_cy + 0.6 * h_name["h"]]
    if not data:
        return []

    # Coluna de nota: pelo cabecalho ou, se faltar (idioma), pelos proprios dados.
    if h_nf:
        nf_cx = h_nf["cx"]
    else:
        ratings = [it for it in data if it["cx"] > name_cx and
                   (re.search(r"\d\s*[.,]\s*\d", it["text"]) or _letters_only(it["text"]) == "ND")]
        if not ratings:
            raise RuntimeError("Nao achei a coluna de nota (NF/rating).")
        ratings.sort(key=lambda it: it["cx"])
        nf_cx = ratings[len(ratings) // 2]["cx"]

    # G/AST ficam logo a direita da nota e coladas. Restringe a busca a essa
    # faixa em X -> ignora 'Goals'/'Assists' de paineis laterais (telas de PC).
    name_gap = max(nf_cx - name_cx, 1.0)
    x_min_num = nf_cx - 0.3 * name_gap
    x_max_num = nf_cx + 1.8 * name_gap
    h_g = _column_center(items, {"G", "GOLS", "GOALS"}, header_cy, band,
                         x_min=x_min_num, x_max=x_max_num)
    h_ast = _column_center(items, {"AST", "ASSIST", "ASSISTS"}, header_cy, band,
                           x_min=x_min_num, x_max=x_max_num)

    # Centros X das colunas (deriva os que faltarem).
    pos_cx = h_pos["cx"] if h_pos else name_cx - (nf_cx - name_cx)
    # O cabecalho 'G' costuma nao ser lido (letra sozinha). Deriva com seguranca:
    if h_g and h_ast:
        g_cx, ast_cx = h_g["cx"], h_ast["cx"]
    elif h_ast:                       # so AST -> G fica no meio entre NF e AST
        ast_cx = h_ast["cx"]
        g_cx = (nf_cx + ast_cx) / 2
    elif h_g:                         # so G -> espelha o passo NF->G para o AST
        g_cx = h_g["cx"]
        ast_cx = g_cx + (g_cx - nf_cx)
    else:                             # nenhum -> espacamento regular a partir do NF
        g_cx = nf_cx + (nf_cx - name_cx) * 0.6
        ast_cx = g_cx + (g_cx - nf_cx)
    centers = {"POS": pos_cx, "Name": name_cx, "NF": nf_cx, "G": g_cx, "AST": ast_cx}

    right_limit = ast_cx + 0.9 * (ast_cx - g_cx)   # ignora painel da direita
    left_limit = pos_cx - 0.9 * (name_cx - pos_cx)
    data = [it for it in data if left_limit <= it["cx"] <= right_limit]
    if not data:
        return []

    def column_of(it):
        return min(centers, key=lambda c: abs(it["cx"] - centers[c]))

    median_h = sorted(it["h"] for it in data)[len(data) // 2]

    # Passo entre linhas = mediana das distancias entre notas (coluna NF, 1/jogador).
    nf_cys = sorted(it["cy"] for it in data if column_of(it) == "NF")
    gaps = [b - a for a, b in zip(nf_cys, nf_cys[1:]) if b - a > 0.3 * median_h]
    row_step = sorted(gaps)[len(gaps) // 2] if gaps else 2.0 * median_h

    # Ancora cada linha na coluna Nome (1 grupo por jogador, bem centrado na
    # linha). Agrupar por 'gap' cru falha: o POS da linha de baixo fica quase tao
    # perto da nota de cima quanto da propria -> as linhas se encadeavam. Ancorar
    # no nome e atribuir cada token ao nome mais proximo (em Y) evita isso.
    names = sorted((it for it in data if column_of(it) == "Name"),
                   key=lambda t: t["cy"])
    if not names:
        return []
    anchors = [[names[0]]]
    for it in names[1:]:
        if it["cy"] - anchors[-1][-1]["cy"] <= 0.35 * row_step:
            anchors[-1].append(it)          # mesmo nome (ex.: 'F.' + 'Mendy')
        else:
            anchors.append([it])
    anchor_cy = [sum(t["cy"] for t in a) / len(a) for a in anchors]

    rows = [[] for _ in anchor_cy]
    for it in data:
        k = min(range(len(anchor_cy)), key=lambda i: abs(it["cy"] - anchor_cy[i]))
        if abs(it["cy"] - anchor_cy[k]) <= 0.75 * row_step:   # descarta rodape solto
            rows[k].append(it)

    # Centro X do recorte: prefere a mediana dos digitos JA lidos na coluna (mais
    # fiel que o cabecalho, que costuma ficar deslocado dos dados); senao, header.
    def _data_cx(column):
        xs = sorted(it["cx"] for it in data
                    if column_of(it) == column and re.search(r"\d", it["text"]))
        return xs[len(xs) // 2] if len(xs) >= 2 else None
    g_cx_crop = _data_cx("G") or g_cx
    ast_cx_crop = _data_cx("AST") or ast_cx

    # Tamanho da celula p/ a 2a passada (recorte) de G e AST.
    spacing = min(abs(g_cx - nf_cx), abs(ast_cx - g_cx))
    cell_w = max(0.45 * spacing, 0.7 * median_h)
    cell_h = 0.85 * median_h

    players = []
    for row in rows:
        col = {"POS": [], "Name": [], "NF": [], "G": [], "AST": []}
        for it in sorted(row, key=lambda it: it["cx"]):
            col[column_of(it)].append(it)

        pos = _letters_only(" ".join(t["text"] for t in col["POS"]))
        name = clean_name(" ".join(t["text"] for t in col["Name"]))
        nf = None
        for t in col["NF"]:
            nf = normalize_rating(t["text"])
            if nf is not None:
                break

        # Descarta cabecalho/rodape e linhas sem nota ANTES da 2a passada (OCR).
        if not name or _letters_only(name) in NOT_A_PLAYER:
            continue
        if nf is None:
            continue

        # G e AST: recorta a celula e le so digitos; se falhar, usa a global.
        # O Y e ancorado na linha do NF (os digitos ficam alinhados com a nota,
        # nao na media da linha, que POS/Nome puxam pra cima).
        cy_num = (sum(t["cy"] for t in col["NF"]) / len(col["NF"])
                  if col["NF"] else sum(t["cy"] for t in row) / len(row))
        g_cell = ocr_digit_cell(img, g_cx_crop, cy_num, cell_w, cell_h)
        ast_cell = ocr_digit_cell(img, ast_cx_crop, cy_num, cell_w, cell_h)
        g = g_cell if g_cell is not None else normalize_count(
            " ".join(t["text"] for t in col["G"]))
        ast = ast_cell if ast_cell is not None else normalize_count(
            " ".join(t["text"] for t in col["AST"]))

        players.append({"POS": pos, "Name": name, "NF": nf, "G": g, "AST": ast})
    return players


def players_to_csv_bytes(players: list[dict]) -> bytes:
    """Serializa as linhas de jogadores em CSV (UTF-8 com BOM)."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["POS", "Name", "NF", "G", "AST"])
    writer.writeheader()
    writer.writerows(players)
    return buffer.getvalue().encode("utf-8-sig")


def process_image_to_csv_bytes(image_path: str) -> bytes:
    """Roda o OCR na imagem e devolve o CSV correspondente em bytes."""
    print(f"[info] lendo: {image_path}")
    items = read_image(image_path)
    img = cv2.imread(image_path)
    players = extract(items, img)

    print(f"\n{'POS':<5} {'Name':<16} {'NF':>5} {'G':>3} {'AST':>4}")
    print("-" * 36)
    for p in players:
        print(f"{p['POS']:<5} {p['Name']:<16} {str(p['NF']):>5} {p['G']:>3} {p['AST']:>4}")

    csv_bytes = players_to_csv_bytes(players)
    print(f"\n[info] {len(players)} jogadores reconhecidos no OCR")
    return csv_bytes


def process_image(image_path):
    csv_bytes = process_image_to_csv_bytes(image_path)
    with open(CSV_PATH, "wb") as f:
        f.write(csv_bytes)
    print(f"[info] CSV salvo em: {CSV_PATH}")


if __name__ == "__main__":
    image_path = os.path.join(BASE_DIR, "leocardo-5.jpeg")
    process_image(image_path)
