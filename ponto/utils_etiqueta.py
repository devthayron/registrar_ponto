import io
from PIL import Image, ImageDraw, ImageFont
import qrcode

def gerar_etiqueta(nome_colaborador, nome_lider, dados_qr):  # nome_lider ainda é ignorado
    folha_largura = 794
    folha_altura = 1123

    etiqueta_largura = 400
    etiqueta_altura = 200
    margem_superior = 1

    folha = Image.new('RGB', (folha_largura, folha_altura), 'white')
    draw = ImageDraw.Draw(folha)

    etiqueta = Image.new('RGB', (etiqueta_largura, etiqueta_altura), 'white')
    etiqueta_draw = ImageDraw.Draw(etiqueta)

    try:
        fonte = ImageFont.truetype("arial.ttf", 10)  
    except IOError:
        fonte = ImageFont.load_default()

    texto_colaborador = f"{nome_colaborador}"
    bbox_colaborador = fonte.getbbox(texto_colaborador)
    largura_colaborador = bbox_colaborador[2] - bbox_colaborador[0]

    centro = etiqueta_largura // 2
    x_colaborador = centro - (largura_colaborador // 2)

    etiqueta_draw.text((x_colaborador, 10), texto_colaborador, font=fonte, fill='black')

    qr = qrcode.make(dados_qr)
    qr = qr.resize((120, 120))
    x_qr = centro - (qr.width // 2)
    etiqueta.paste(qr, (x_qr, 45))  # ajustado um pouco para a nova altura da fonte

    pos_x = (folha_largura - etiqueta_largura) // 2
    pos_y = margem_superior
    folha.paste(etiqueta, (pos_x, pos_y))

    buffer = io.BytesIO()
    folha.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer
