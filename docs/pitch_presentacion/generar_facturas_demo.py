"""
Generador de facturas de demostración para el pitch de Blinka PayAgent (V3).
Crea documentos limpios y nítidos en formato PNG y PDF:
1. Cuenta_Cobro_Biometrico.pdf / .png (450,000 COP -> $107.14 USD -> SCALED_TO_HUMAN por HITL-02)
2. Factura_AWS_Cloud_Octubre.pdf / .png (1,200,000 COP -> $285.71 USD -> AUTO_APPROVED)
3. Factura_Logistica_MX_Oct.pdf / .png (117,000 MXN -> $6,000.00 USD -> SCALED_TO_HUMAN por HITL-01)
"""

import os
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "facturas_demo")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Paleta
NAVY = (11, 28, 48)
TEAL = (43, 156, 174)
STEEL = (29, 53, 87)
MUTED = (100, 116, 139)
LIGHT_BG = (248, 250, 252)
BORDER_COLOR = (226, 232, 240)
WHITE = (255, 255, 255)
DARK = (15, 23, 42)


def get_font(size: int, bold: bool = False):
    font_paths = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf" if bold else "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
    ]
    for p in font_paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def crear_factura_biometrico():
    w, h = 1200, 1600
    img = Image.new("RGB", (w, h), WHITE)
    draw = ImageDraw.Draw(img)

    # Franja superior
    draw.rectangle([0, 0, w, 24], fill=TEAL)

    # Encabezado
    f_h1 = get_font(34, bold=True)
    f_h2 = get_font(20, bold=True)
    f_body = get_font(18, bold=False)
    f_body_bold = get_font(18, bold=True)
    f_mono = get_font(18, bold=True)
    f_mono_large = get_font(32, bold=True)

    # Proveedor (Proveedor no registrado en seed -> HITL-02)
    draw.text((70, 70), "TÉCNICO DE URGENCIAS Y BIOMETRÍA S.A.S.", fill=NAVY, font=f_h1)
    draw.text((70, 120), "NIT: 901.888.777-1 | Régimen Común", fill=MUTED, font=f_body_bold)
    draw.text((70, 150), "Servicio Técnico, Mantenimiento de Hardware y Seguridad de Acceso", fill=MUTED, font=f_body)
    draw.text((70, 180), "Calle 93B # 13-45, Of. 402, Bogotá D.C., Colombia", fill=MUTED, font=f_body)

    # Caja de Documento
    draw.rounded_rectangle([760, 65, 1130, 210], radius=8, outline=BORDER_COLOR, width=2, fill=LIGHT_BG)
    draw.text((790, 85), "CUENTA DE COBRO", fill=NAVY, font=f_h2)
    draw.text((790, 120), "No. CC-2026-891", fill=TEAL, font=f_mono)
    draw.text((790, 155), "Fecha: 17 de Octubre de 2026", fill=DARK, font=f_body)

    # Línea divisoria
    draw.line([70, 240, 1130, 240], fill=BORDER_COLOR, width=2)

    # Datos del Cliente
    draw.text((70, 270), "COBRADA A:", fill=MUTED, font=f_body_bold)
    draw.text((70, 305), "Blinka Tech Corp S.A.S.", fill=NAVY, font=f_h2)
    draw.text((70, 340), "NIT: 901.555.444-2", fill=DARK, font=f_body)
    draw.text((70, 370), "Dirección: Cra 11 # 82-01, Piso 6, Bogotá D.C.", fill=DARK, font=f_body)

    # Datos adicionales
    draw.text((650, 270), "DETALLES DEL SERVICIO:", fill=MUTED, font=f_body_bold)
    draw.text((650, 305), "Atención: Tesorería y Pagos Corporativos", fill=DARK, font=f_body)
    draw.text((650, 340), "Vencimiento: Inmediato / Contraentrega", fill=DARK, font=f_body)
    draw.text((650, 370), "Moneda: COP (Pesos Colombianos)", fill=DARK, font=f_body_bold)

    # Tabla de Concepto
    draw.rounded_rectangle([70, 440, 1130, 500], radius=6, fill=NAVY)
    draw.text((95, 460), "DESCRIPCIÓN DEL SERVICIO", fill=WHITE, font=f_body_bold)
    draw.text((680, 460), "CANT.", fill=WHITE, font=f_body_bold)
    draw.text((800, 460), "VALOR UNIT.", fill=WHITE, font=f_body_bold)
    draw.text((990, 460), "TOTAL COP", fill=WHITE, font=f_body_bold)

    # Fila 1
    draw.rounded_rectangle([70, 510, 1130, 670], radius=6, outline=BORDER_COLOR, width=1, fill=WHITE)
    draw.text((95, 535), "Reparación y calibración de urgencia lector biométrico de acceso", fill=DARK, font=f_body_bold)
    draw.text((95, 565), "Atención imprevista en sábado jornada matutina (08:00 AM).", fill=MUTED, font=f_body)
    draw.text((95, 595), "Reemplazo de módulo sensor óptico y reinstalación de firmware.", fill=MUTED, font=f_body)
    draw.text((695, 545), "1", fill=DARK, font=f_body)
    draw.text((790, 545), "$ 450.000", fill=DARK, font=f_body)
    draw.text((980, 545), "$ 450.000", fill=DARK, font=f_body_bold)

    # Resumen Total
    draw.rounded_rectangle([700, 700, 1130, 830], radius=8, outline=BORDER_COLOR, width=2, fill=LIGHT_BG)
    draw.text((730, 725), "Subtotal:", fill=MUTED, font=f_body)
    draw.text((980, 725), "$ 450.000 COP", fill=DARK, font=f_body)
    draw.text((730, 765), "TOTAL A PAGAR:", fill=NAVY, font=f_h2)
    draw.text((950, 760), "$ 450.000 COP", fill=TEAL, font=f_mono_large)

    # Instrucciones Bancarias
    draw.rounded_rectangle([70, 870, 1130, 1070], radius=8, outline=BORDER_COLOR, width=1, fill=WHITE)
    draw.text((100, 900), "INSTRUCCIONES DE PAGO:", fill=NAVY, font=f_h2)
    draw.text((100, 940), "Banco: Bancolombia", fill=DARK, font=f_body)
    draw.text((100, 970), "Tipo de Cuenta: Cuenta de Ahorros", fill=DARK, font=f_body)
    draw.text((100, 1000), "Número de Cuenta: CO-BANCOLOMBIA-20198765432", fill=STEEL, font=f_mono)
    draw.text((100, 1030), "Titular: Técnico de Urgencias y Biometría S.A.S. (NIT 901.888.777-1)", fill=DARK, font=f_body)

    # Nota de Gobernanza
    draw.text((70, 1140), "Certifico que la presente cuenta de cobro corresponde a servicios técnicos efectivamente prestados.", fill=MUTED, font=f_body)
    draw.text((70, 1170), "Firma Responsable: Ing. Carlos M. Benítez — C.C. 79.845.120", fill=DARK, font=f_body_bold)

    # Guardar
    png_path = os.path.join(OUTPUT_DIR, "Cuenta_Cobro_Biometrico.png")
    pdf_path = os.path.join(OUTPUT_DIR, "Cuenta_Cobro_Biometrico.pdf")
    img.save(png_path)
    img.save(pdf_path, "PDF", resolution=150.0)
    print(f"Creado: {png_path} y {pdf_path}")


def crear_factura_aws():
    w, h = 1200, 1600
    img = Image.new("RGB", (w, h), WHITE)
    draw = ImageDraw.Draw(img)

    # Franja superior
    draw.rectangle([0, 0, w, 24], fill=(255, 153, 0))  # AWS Orange

    f_h1 = get_font(34, bold=True)
    f_h2 = get_font(20, bold=True)
    f_body = get_font(18, bold=False)
    f_body_bold = get_font(18, bold=True)
    f_mono = get_font(18, bold=True)
    f_mono_large = get_font(32, bold=True)

    # Proveedor (Exacto al seed: Amazon Web Services LATAM)
    draw.text((70, 70), "Amazon Web Services LATAM", fill=NAVY, font=f_h1)
    draw.text((70, 120), "Tax ID / NIT: US-91-1646860", fill=MUTED, font=f_body_bold)
    draw.text((70, 150), "Amazon Web Services Inc. - LatAm Regional Operations", fill=MUTED, font=f_body)
    draw.text((70, 180), "410 Terry Avenue North, Seattle, WA 98109, United States", fill=MUTED, font=f_body)

    # Caja Factura
    draw.rounded_rectangle([760, 65, 1130, 210], radius=8, outline=BORDER_COLOR, width=2, fill=LIGHT_BG)
    draw.text((790, 85), "INVOICE / FACTURA", fill=NAVY, font=f_h2)
    draw.text((790, 120), "No. AWS-2026-10-DEMO", fill=(217, 119, 6), font=f_mono)
    draw.text((790, 155), "Date: 17 de Octubre de 2026", fill=DARK, font=f_body)

    draw.line([70, 240, 1130, 240], fill=BORDER_COLOR, width=2)

    # Cliente
    draw.text((70, 270), "FACTURADO A:", fill=MUTED, font=f_body_bold)
    draw.text((70, 305), "Blinka Tech Corp S.A.S.", fill=NAVY, font=f_h2)
    draw.text((70, 340), "Account ID: 404-9821-3310", fill=DARK, font=f_body)
    draw.text((70, 370), "Tax ID: 901.555.444-2 | Bogotá, Colombia", fill=DARK, font=f_body)

    draw.text((650, 270), "DETALLES DEL PERIODO:", fill=MUTED, font=f_body_bold)
    draw.text((650, 305), "Periodo: Octubre 2026 (Mensual)", fill=DARK, font=f_body)
    draw.text((650, 340), "Vencimiento: 15 de Noviembre de 2026", fill=DARK, font=f_body)
    draw.text((650, 370), "Moneda: COP (Tasa ref. 4,200 COP/USD)", fill=DARK, font=f_body_bold)

    # Tabla
    draw.rounded_rectangle([70, 440, 1130, 500], radius=6, fill=NAVY)
    draw.text((95, 460), "SERVICIOS CLOUD AWS (LATAM REGION)", fill=WHITE, font=f_body_bold)
    draw.text((700, 460), "REGIÓN", fill=WHITE, font=f_body_bold)
    draw.text((980, 460), "TOTAL COP", fill=WHITE, font=f_body_bold)

    draw.rounded_rectangle([70, 510, 1130, 680], radius=6, outline=BORDER_COLOR, width=1, fill=WHITE)
    draw.text((95, 535), "Amazon Elastic Compute Cloud (EC2) - Production Cluster", fill=DARK, font=f_body_bold)
    draw.text((95, 565), "Instancias t4g.xlarge, balanceador ALB y storage EBS gp3", fill=MUTED, font=f_body)
    draw.text((700, 545), "us-east-1", fill=DARK, font=f_body)
    draw.text((970, 545), "$ 800.000", fill=DARK, font=f_body)

    draw.text((95, 605), "Amazon Simple Storage Service (S3) & CloudFront CDN", fill=DARK, font=f_body_bold)
    draw.text((95, 635), "Almacenamiento de buckets, data transfer out y cache global", fill=MUTED, font=f_body)
    draw.text((700, 615), "Global", fill=DARK, font=f_body)
    draw.text((970, 615), "$ 400.000", fill=DARK, font=f_body)

    # Resumen
    draw.rounded_rectangle([700, 710, 1130, 840], radius=8, outline=BORDER_COLOR, width=2, fill=LIGHT_BG)
    draw.text((730, 735), "Subtotal COP:", fill=MUTED, font=f_body)
    draw.text((970, 735), "$ 1.200.000 COP", fill=DARK, font=f_body)
    draw.text((730, 775), "TOTAL A PAGAR:", fill=NAVY, font=f_h2)
    draw.text((930, 770), "$ 1.200.000 COP", fill=(217, 119, 6), font=f_mono_large)

    # Cuenta bancaria (del seed: US-CHASE-000123456)
    draw.rounded_rectangle([70, 880, 1130, 1060], radius=8, outline=BORDER_COLOR, width=1, fill=WHITE)
    draw.text((100, 910), "PAYMENT INSTRUCTIONS / INSTRUCCIONES BANCARIAS:", fill=NAVY, font=f_h2)
    draw.text((100, 950), "Bank Name: JPMorgan Chase Bank N.A. (New York, USA)", fill=DARK, font=f_body)
    draw.text((100, 980), "Account Number / Cuenta: US-CHASE-000123456", fill=STEEL, font=f_mono)
    draw.text((100, 1010), "Beneficiary: Amazon Web Services LATAM (Tax ID US-91-1646860)", fill=DARK, font=f_body)

    draw.text((70, 1150), "Terms: Electronic settlement via Blinka PayAgent. Net 30 days.", fill=MUTED, font=f_body)

    png_path = os.path.join(OUTPUT_DIR, "Factura_AWS_Cloud_Octubre.png")
    pdf_path = os.path.join(OUTPUT_DIR, "Factura_AWS_Cloud_Octubre.pdf")
    img.save(png_path)
    img.save(pdf_path, "PDF", resolution=150.0)
    print(f"Creado: {png_path} y {pdf_path}")


def crear_factura_logistica():
    w, h = 1200, 1600
    img = Image.new("RGB", (w, h), WHITE)
    draw = ImageDraw.Draw(img)

    # Franja superior
    draw.rectangle([0, 0, w, 24], fill=(16, 185, 129))  # Emerald

    f_h1 = get_font(34, bold=True)
    f_h2 = get_font(20, bold=True)
    f_body = get_font(18, bold=False)
    f_body_bold = get_font(18, bold=True)
    f_mono = get_font(18, bold=True)
    f_mono_large = get_font(32, bold=True)

    # Proveedor (Exacto al seed: Logística Express MX S.A. de C.V.)
    draw.text((70, 70), "Logística Express MX S.A. de C.V.", fill=NAVY, font=f_h1)
    draw.text((70, 120), "RFC: LEM850101AB1 | Régimen General de Ley", fill=MUTED, font=f_body_bold)
    draw.text((70, 150), "Transporte de Carga Consolidada y Logística Transfronteriza", fill=MUTED, font=f_body)
    draw.text((70, 180), "Av. Paseo de la Reforma 405, Piso 12, Cuauhtémoc, CDMX, México", fill=MUTED, font=f_body)

    # Caja Factura
    draw.rounded_rectangle([760, 65, 1130, 210], radius=8, outline=BORDER_COLOR, width=2, fill=LIGHT_BG)
    draw.text((790, 85), "COMPROBANTE FISCAL", fill=NAVY, font=f_h2)
    draw.text((790, 120), "No. LEM-2026-904", fill=(16, 185, 129), font=f_mono)
    draw.text((790, 155), "Fecha: 17 de Octubre de 2026", fill=DARK, font=f_body)

    draw.line([70, 240, 1130, 240], fill=BORDER_COLOR, width=2)

    # Cliente
    draw.text((70, 270), "RECEPTOR / CLIENTE:", fill=MUTED, font=f_body_bold)
    draw.text((70, 305), "Blinka Tech Corp S.A.S.", fill=NAVY, font=f_h2)
    draw.text((70, 340), "RFC / Tax ID Extranjero: 901.555.444-2", fill=DARK, font=f_body)
    draw.text((70, 370), "Uso CFDI: G03 - Gastos en general", fill=DARK, font=f_body)

    draw.text((650, 270), "CONDICIONES COMERCIALES:", fill=MUTED, font=f_body_bold)
    draw.text((650, 305), "Contrato Marco: Tarifa pactada $15,000 USD", fill=DARK, font=f_body)
    draw.text((650, 340), "Vencimiento: 30 de Noviembre de 2026", fill=DARK, font=f_body)
    draw.text((650, 370), "Moneda: MXN (Pesos Mexicanos)", fill=DARK, font=f_body_bold)

    # Tabla
    draw.rounded_rectangle([70, 440, 1130, 500], radius=6, fill=NAVY)
    draw.text((95, 460), "CONCEPTO DE TRANSPORTE Y OPERACIÓN", fill=WHITE, font=f_body_bold)
    draw.text((700, 460), "TIPO SERVICIO", fill=WHITE, font=f_body_bold)
    draw.text((970, 460), "TOTAL MXN", fill=WHITE, font=f_body_bold)

    draw.rounded_rectangle([70, 510, 1130, 670], radius=6, outline=BORDER_COLOR, width=1, fill=WHITE)
    draw.text((95, 535), "Servicio de flete terrestre internacional consolidado LTL", fill=DARK, font=f_body_bold)
    draw.text((95, 565), "Ruta Monterrey - Laredo - CDMX. Seguro de carga incluido.", fill=MUTED, font=f_body)
    draw.text((700, 545), "Flete Terrestre", fill=DARK, font=f_body)
    draw.text((960, 545), "$ 117.000", fill=DARK, font=f_body_bold)

    # Resumen
    draw.rounded_rectangle([700, 700, 1130, 830], radius=8, outline=BORDER_COLOR, width=2, fill=LIGHT_BG)
    draw.text((730, 725), "Subtotal MXN:", fill=MUTED, font=f_body)
    draw.text((960, 725), "$ 117.000 MXN", fill=DARK, font=f_body)
    draw.text((730, 765), "TOTAL A PAGAR:", fill=NAVY, font=f_h2)
    draw.text((930, 760), "$ 117.000 MXN", fill=(16, 185, 129), font=f_mono_large)

    # Cuenta bancaria (del seed: MX-BBVA-012180001234567890)
    draw.rounded_rectangle([70, 870, 1130, 1050], radius=8, outline=BORDER_COLOR, width=1, fill=WHITE)
    draw.text((100, 900), "DATOS DE TRANSFERENCIA SPEI:", fill=NAVY, font=f_h2)
    draw.text((100, 940), "Banco Receptor: BBVA México", fill=DARK, font=f_body)
    draw.text((100, 970), "CLABE Interbancaria: MX-BBVA-012180001234567890", fill=STEEL, font=f_mono)
    draw.text((100, 1000), "Beneficiario: Logística Express MX S.A. de C.V. (RFC LEM850101AB1)", fill=DARK, font=f_body)

    draw.text((70, 1140), "Este comprobante será procesado mediante la tubería de pagos de Blinka PayAgent.", fill=MUTED, font=f_body)

    png_path = os.path.join(OUTPUT_DIR, "Factura_Logistica_MX_Oct.png")
    pdf_path = os.path.join(OUTPUT_DIR, "Factura_Logistica_MX_Oct.pdf")
    img.save(png_path)
    img.save(pdf_path, "PDF", resolution=150.0)
    print(f"Creado: {png_path} y {pdf_path}")


if __name__ == "__main__":
    crear_factura_biometrico()
    crear_factura_aws()
    crear_factura_logistica()
