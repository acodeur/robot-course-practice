"""
生成作业 3.2 PDF 文档
包含：设计思路、SolidWorks 导出配置、URDF 结构、RViz 验证截图
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "images")
OUT_PDF = os.path.join(BASE_DIR, "homework_3_2.pdf")

# ── 注册中文字体 ──
FONT_PATHS = [
    ("SimSun", "C:/Windows/Fonts/simsun.ttc"),
    ("SimHei", "C:/Windows/Fonts/simhei.ttf"),
    ("MSYaHei", "C:/Windows/Fonts/msyh.ttc"),
]

CN_FONT = "Helvetica"  # fallback
CN_FONT_BOLD = "Helvetica-Bold"

for name, path in FONT_PATHS:
    if os.path.exists(path):
        try:
            pdfmetrics.registerFont(TTFont(name, path))
            CN_FONT = name
            CN_FONT_BOLD = name
            break
        except Exception:
            continue


def build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'CNTitle', parent=styles['Title'],
        fontName=CN_FONT_BOLD, fontSize=22, leading=30,
        spaceAfter=6*mm, alignment=TA_CENTER,
        textColor=HexColor('#1a1a2e'),
    ))
    styles.add(ParagraphStyle(
        'CNSubtitle', parent=styles['Normal'],
        fontName=CN_FONT, fontSize=11, leading=16,
        spaceAfter=10*mm, alignment=TA_CENTER,
        textColor=HexColor('#666666'),
    ))
    styles.add(ParagraphStyle(
        'CNHeading1', parent=styles['Heading1'],
        fontName=CN_FONT_BOLD, fontSize=16, leading=22,
        spaceBefore=8*mm, spaceAfter=4*mm,
        textColor=HexColor('#16213e'),
        borderWidth=0, borderColor=HexColor('#3366CC'),
        borderPadding=3,
    ))
    styles.add(ParagraphStyle(
        'CNHeading2', parent=styles['Heading2'],
        fontName=CN_FONT_BOLD, fontSize=13, leading=18,
        spaceBefore=5*mm, spaceAfter=3*mm,
        textColor=HexColor('#0f3460'),
    ))
    styles.add(ParagraphStyle(
        'CNBody', parent=styles['Normal'],
        fontName=CN_FONT, fontSize=10.5, leading=17,
        spaceAfter=2*mm, alignment=TA_JUSTIFY,
        textColor=HexColor('#333333'),
    ))
    styles.add(ParagraphStyle(
        'CNCaption', parent=styles['Normal'],
        fontName=CN_FONT, fontSize=9, leading=13,
        spaceBefore=2*mm, spaceAfter=5*mm, alignment=TA_CENTER,
        textColor=HexColor('#888888'),
    ))
    styles.add(ParagraphStyle(
        'CNCode', parent=styles['Code'],
        fontName='Courier', fontSize=8, leading=11,
        spaceAfter=3*mm, leftIndent=10*mm,
        textColor=HexColor('#2d2d2d'),
        backColor=HexColor('#f5f5f5'),
        borderWidth=0.5, borderColor=HexColor('#dddddd'),
        borderPadding=5,
    ))
    return styles


def add_image(story, filename, caption, width=140*mm, styles=None):
    img_path = os.path.join(IMG_DIR, filename)
    if os.path.exists(img_path):
        img = Image(img_path, width=width, height=width * 0.8)
        img.hAlign = 'CENTER'
        story.append(img)
        if styles:
            story.append(Paragraph(caption, styles['CNCaption']))
    else:
        if styles:
            story.append(Paragraph(f"[Image not found: {filename}]", styles['CNBody']))


def add_hr(story):
    story.append(Spacer(1, 3*mm))
    story.append(HRFlowable(width="90%", thickness=0.5, color=HexColor('#cccccc')))
    story.append(Spacer(1, 3*mm))


def build_pdf():
    doc = SimpleDocTemplate(
        OUT_PDF, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
    )
    styles = build_styles()
    story = []

    # ════════════════════ 封面 ════════════════════
    story.append(Spacer(1, 40*mm))
    story.append(Paragraph("CAD\u5bfc\u51fa\u5b9e\u6218\uff1a5-DOF\u673a\u68b0\u81c2\u5efa\u6a21\u4e0eURDF\u5bfc\u51fa", styles['CNTitle']))
    story.append(Paragraph("\u4eba\u5f62\u673a\u5668\u4eba\u7efc\u5408\u5b9e\u8df5\u8bfe (2025\u5e741\u671f) - \u4f5c\u4e1a3.2", styles['CNSubtitle']))
    story.append(Spacer(1, 15*mm))
    story.append(Paragraph(
        "\u8bbe\u8ba1\u4e00\u4e2a\u4e0d\u5c11\u4e8e5\u4e2a\u5173\u8282\u7684\u673a\u5668\u4eba\u6a21\u578b\uff0c"
        "\u4f7f\u7528\u5bfc\u51fa\u5de5\u5177\u5c06\u5176\u8f6c\u5316\u4e3a\u6807\u51c6URDF\u6587\u4ef6\uff0c"
        "\u901a\u8fc7ROS\u53ef\u89c6\u5316\u4eff\u771f\u9a8c\u8bc1\u5176\u5750\u6807\u7cfb\u53ca\u8fd0\u52a8\u5b66\u8fde\u901a\u6027\u7684\u6b63\u786e\u6027\u3002",
        styles['CNBody']
    ))
    story.append(PageBreak())

    # ════════════════════ 目录概览 ════════════════════
    story.append(Paragraph("\u76ee\u5f55", styles['CNHeading1']))
    toc_items = [
        "\u4e00\u3001\u8bbe\u8ba1\u601d\u8def\u4e0e\u673a\u68b0\u81c2\u7ed3\u6784\u8bbe\u8ba1",
        "\u4e8c\u3001SolidWorks VBA\u5b8f\u81ea\u52a8\u5316\u5efa\u6a21",
        "\u4e09\u3001SolidWorks\u5efa\u6a21\u4e0eSTL\u5bfc\u51fa\u64cd\u4f5c",
        "\u56db\u3001URDF\u6587\u4ef6\u7f16\u5199\u4e0e\u914d\u7f6e",
        "\u4e94\u3001ROS/RViz\u53ef\u89c6\u5316\u9a8c\u8bc1",
        "\u516d\u3001\u8fd0\u52a8\u5b66\u8fde\u901a\u6027\u9a8c\u8bc1",
        "\u4e03\u3001\u603b\u7ed3",
    ]
    for item in toc_items:
        story.append(Paragraph(item, styles['CNBody']))
    story.append(PageBreak())

    # ════════════════════ 一、设计思路 ════════════════════
    story.append(Paragraph("\u4e00\u3001\u8bbe\u8ba1\u601d\u8def\u4e0e\u673a\u68b0\u81c2\u7ed3\u6784\u8bbe\u8ba1", styles['CNHeading1']))
    add_hr(story)

    story.append(Paragraph("1.1 \u8bbe\u8ba1\u76ee\u6807", styles['CNHeading2']))
    story.append(Paragraph(
        "\u8bbe\u8ba1\u4e00\u4e2a\u5177\u67095\u4e2a\u65cb\u8f6c\u5173\u8282\u7684\u4e32\u8054\u673a\u68b0\u81c2\uff0c"
        "\u6db5\u76d6\u5e38\u89c1\u7684\u5de5\u4e1a\u673a\u68b0\u81c2\u81ea\u7531\u5ea6\u914d\u7f6e\uff1a"
        "\u5e95\u5ea7\u65cb\u8f6c\u3001\u80a9\u90e8\u4fef\u4ef0\u3001\u8098\u90e8\u5f2f\u66f2\u3001\u8155\u90e8\u4fef\u4ef0\u3001\u8155\u90e8\u65cb\u8f6c\u3002"
        "\u8be5\u914d\u7f6e\u80fd\u591f\u8ba9\u672b\u7aef\u6267\u884c\u5668\u5728\u5de5\u4f5c\u7a7a\u95f4\u5185\u5b9e\u73b0\u4f4d\u7f6e\u548c\u59ff\u6001\u7684\u7075\u6d3b\u63a7\u5236\u3002",
        styles['CNBody']
    ))

    story.append(Paragraph("1.2 \u8fd0\u52a8\u5b66\u94fe\u8bbe\u8ba1", styles['CNHeading2']))
    story.append(Paragraph(
        "\u673a\u68b0\u81c2\u91c7\u7528\u7ecf\u5178\u7684RRRRR\u4e32\u8054\u6784\u578b\uff08\u5168\u90e8\u4e3a\u65cb\u8f6c\u5173\u8282\uff09\uff0c"
        "\u8fd0\u52a8\u5b66\u94fe\u4ece\u5e95\u5ea7\u5230\u672b\u7aef\u6267\u884c\u5668\u4f9d\u6b21\u4e3a\uff1a",
        styles['CNBody']
    ))

    # Link-Joint table
    link_data = [
        ['\u90e8\u4ef6', '\u51e0\u4f55\u5f62\u72b6', '\u5c3a\u5bf8 (m)', '\u5173\u8282', '\u65cb\u8f6c\u8f74'],
        ['base_link (\u5e95\u5ea7)', '\u5706\u67f1\u4f53', 'R=0.12, H=0.08', '-', '-'],
        ['link_1 (\u80a9\u90e8\u8f6c\u53f0)', '\u5706\u67f1\u4f53', 'R=0.06, H=0.06', 'base_yaw', 'Z\u8f74'],
        ['link_2 (\u5927\u81c2)', '\u957f\u65b9\u4f53', '0.08x0.06x0.30', 'shoulder_pitch', 'Y\u8f74'],
        ['link_3 (\u5c0f\u81c2)', '\u5706\u67f1\u4f53', 'R=0.035, H=0.25', 'elbow_pitch', 'Y\u8f74'],
        ['link_4 (\u8155\u90e8)', '\u5706\u67f1\u4f53', 'R=0.03, H=0.12', 'wrist_pitch', 'Y\u8f74'],
        ['link_5 (\u672b\u7aef)', '\u957f\u65b9\u4f53', '0.06x0.08x0.04', 'wrist_roll', 'Z\u8f74'],
    ]
    t = Table(link_data, colWidths=[35*mm, 25*mm, 35*mm, 32*mm, 18*mm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), CN_FONT),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (-1, 0), CN_FONT_BOLD),
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3366CC')),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#FFFFFF'), HexColor('#F0F4F8')]),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Paragraph("\u88681\uff1a\u673a\u68b0\u81c2\u8fde\u6746-\u5173\u8282\u914d\u7f6e\u8868", styles['CNCaption']))

    story.append(Paragraph("1.3 URDF\u6811\u7ed3\u6784", styles['CNHeading2']))
    story.append(Paragraph(
        "\u4e0b\u56fe\u5c55\u793a\u4e86\u673a\u68b0\u81c2\u7684URDF Link-Joint\u6811\u7ed3\u6784\uff0c"
        "\u6240\u6709\u5173\u8282\u5747\u4e3arevolute\u7c7b\u578b\uff0c\u5f62\u6210\u4e00\u6761\u4e32\u8054\u8fd0\u52a8\u5b66\u94fe\uff1a",
        styles['CNBody']
    ))
    add_image(story, "urdf_tree.png", "\u56fe1\uff1aURDF Link-Joint \u6811\u7ed3\u6784\u56fe", width=120*mm, styles=styles)

    story.append(Paragraph("1.4 DH\u53c2\u6570", styles['CNHeading2']))
    story.append(Paragraph(
        "\u91c7\u7528\u6539\u8fdbDH\u53c2\u6570\u6cd5\u63cf\u8ff0\u5404\u5173\u8282\u7684\u8fd0\u52a8\u5b66\u53c2\u6570\uff1a",
        styles['CNBody']
    ))
    add_image(story, "dh_table.png", "\u56fe2\uff1a\u6539\u8fdbDH\u53c2\u6570\u8868", width=150*mm, styles=styles)

    story.append(PageBreak())

    # ════════════════════ 二、VBA宏自动化建模 ════════════════════
    story.append(Paragraph("\u4e8c\u3001SolidWorks VBA\u5b8f\u81ea\u52a8\u5316\u5efa\u6a21", styles['CNHeading1']))
    add_hr(story)

    story.append(Paragraph("2.1 VBA\u5b8f\u6982\u8ff0", styles['CNHeading2']))
    story.append(Paragraph(
        "\u4e3a\u5b9e\u73b0\u673a\u68b0\u81c2\u6a21\u578b\u7684\u81ea\u52a8\u5316\u521b\u5efa\uff0c\u7f16\u5199\u4e86 SolidWorks VBA \u5b8f\u7a0b\u5e8f "
        "<b>Create5DOFRobot.vba</b>\u3002\u8be5\u5b8f\u53ef\u901a\u8fc7 SolidWorks \u7684\u5b8f\u52a0\u8f7d\u529f\u80fd\u4e00\u952e\u8fd0\u884c\uff0c"
        "\u81ea\u52a8\u5b8c\u6210\u4ee5\u4e0b\u5168\u90e8\u5de5\u4f5c\uff1a",
        styles['CNBody']
    ))
    story.append(Paragraph(
        "- \u521b\u5efa 6 \u4e2a\u72ec\u7acb\u96f6\u4ef6\uff08base_link, link_1 ~ link_5\uff09<br/>"
        "- \u6bcf\u4e2a\u96f6\u4ef6\u81ea\u52a8\u8bbe\u7f6e\u989c\u8272\uff08\u7070\u3001\u84dd\u3001\u6a59\u3001\u6d45\u84dd\u3001\u7ea2\u3001\u7eff\uff09<br/>"
        "- \u81ea\u52a8\u4fdd\u5b58 SLDPRT \u96f6\u4ef6\u5e76\u5bfc\u51fa STL \u6587\u4ef6<br/>"
        "- \u521b\u5efa\u88c5\u914d\u4f53 arm_5dof.SLDASM\uff0c\u5c06\u6240\u6709\u96f6\u4ef6\u6309\u8fd0\u52a8\u5b66\u94fe\u5806\u53e0\u88c5\u914d",
        styles['CNBody']
    ))

    story.append(Paragraph("2.2 VBA\u5b8f\u52a0\u8f7d\u4e0e\u8fd0\u884c\u6b65\u9aa4", styles['CNHeading2']))
    vba_run_steps = [
        "<b>\u6b65\u9aa41</b>\uff1a\u6253\u5f00 SolidWorks \u8f6f\u4ef6",
        "<b>\u6b65\u9aa42</b>\uff1a\u83dc\u5355\u680f \u2192 \u5de5\u5177(Tools) \u2192 \u5b8f(Macro) \u2192 \u8fd0\u884c(Run)\uff0c\u6216\u5feb\u6377\u952e Alt+F8",
        "<b>\u6b65\u9aa43</b>\uff1a\u6d4f\u89c8\u5e76\u9009\u62e9 Create5DOFRobot.vba \u6587\u4ef6",
        "<b>\u6b65\u9aa44</b>\uff1a\u5728\u5b8f\u5217\u8868\u4e2d\u9009\u62e9 \"main\" \u8fc7\u7a0b\uff0c\u70b9\u51fb\"\u8fd0\u884c\"",
        "<b>\u6b65\u9aa45</b>\uff1a\u7b49\u5f85\u5b8f\u6267\u884c\u5b8c\u6210\uff0c\u5f39\u51fa\u5b8c\u6210\u63d0\u793a\u6846",
    ]
    for step in vba_run_steps:
        story.append(Paragraph(step, styles['CNBody']))
        story.append(Spacer(1, 1*mm))

    story.append(Paragraph("2.3 VBA\u5b8f\u6838\u5fc3\u4ee3\u7801\u89e3\u6790", styles['CNHeading2']))

    story.append(Paragraph(
        "<b>\u96f6\u4ef6\u521b\u5efa\u6d41\u7a0b</b>\uff1a\u6bcf\u4e2a\u96f6\u4ef6\u7684\u521b\u5efa\u8fc7\u7a0b\u9075\u5faa\u76f8\u540c\u6a21\u5f0f\uff1a"
        "\u65b0\u5efa\u96f6\u4ef6 \u2192 \u9009\u62e9\u57fa\u51c6\u9762 \u2192 \u7ed8\u5236\u8349\u56fe \u2192 \u62c9\u4f38\u51f8\u53f0 \u2192 \u8bbe\u7f6e\u989c\u8272 \u2192 \u4fdd\u5b58/\u5bfc\u51fa\u3002",
        styles['CNBody']
    ))

    vba_snippet1 = (
        "' ===== \u521b\u5efa\u5706\u67f1\u4f53\u96f6\u4ef6\u7684\u6838\u5fc3\u903b\u8f91 =====<br/>"
        "Sub CreateCylinder(planeName, radius, height)<br/>"
        "&nbsp;&nbsp;' 1. \u9009\u62e9\u57fa\u51c6\u9762<br/>"
        "&nbsp;&nbsp;swModel.Extension.SelectByID2 _<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;planeName, \"PLANE\", 0, 0, 0, ...<br/>"
        "&nbsp;&nbsp;swSketchMgr.InsertSketch True<br/>"
        "&nbsp;&nbsp;' 2. \u7ed8\u5236\u5706<br/>"
        "&nbsp;&nbsp;swSketchMgr.CreateCircle _<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;0, 0, 0, radius, 0, 0<br/>"
        "&nbsp;&nbsp;swSketchMgr.InsertSketch True<br/>"
        "&nbsp;&nbsp;' 3. \u62c9\u4f38\u51f8\u53f0<br/>"
        "&nbsp;&nbsp;swFeatMgr.FeatureExtrusion3 _<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;True, False, False, _<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;0, 0, height, ...<br/>"
        "End Sub"
    )
    story.append(Paragraph(vba_snippet1, styles['CNCode']))

    story.append(Paragraph(
        "<b>\u88c5\u914d\u4f53\u521b\u5efa</b>\uff1a\u901a\u8fc7 AddComponent5 \u65b9\u6cd5\u5c06\u96f6\u4ef6\u6309 Z \u8f74\u7d2f\u8ba1\u504f\u79fb\u63d2\u5165\uff1a",
        styles['CNBody']
    ))

    vba_snippet2 = (
        "' ===== \u88c5\u914d\u4f53\u521b\u5efa\u6838\u5fc3\u903b\u8f91 =====<br/>"
        "Dim currentZ As Double: currentZ = 0<br/>"
        "For i = 0 To 5<br/>"
        "&nbsp;&nbsp;Set swComponent = swAssembly.AddComponent5( _<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;partPath, 0, \"\", False, \"\", _<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;0, currentZ, 0)  ' Z\u8f74\u504f\u79fb<br/>"
        "&nbsp;&nbsp;currentZ = currentZ + partHeights(i)<br/>"
        "Next i"
    )
    story.append(Paragraph(vba_snippet2, styles['CNCode']))

    story.append(Paragraph(
        "<b>STL\u5bfc\u51fa\u914d\u7f6e</b>\uff1a\u5b8f\u7a0b\u5e8f\u81ea\u52a8\u8bbe\u7f6e STL \u5bfc\u51fa\u53c2\u6570\uff08\u4e8c\u8fdb\u5236\u683c\u5f0f\u3001\u7c73\u4e3a\u5355\u4f4d\uff09\uff0c"
        "\u786e\u4fdd\u4e0e URDF \u5355\u4f4d\u4e00\u81f4\uff1a",
        styles['CNBody']
    ))

    vba_snippet3 = (
        "' ===== STL\u5bfc\u51fa\u53c2\u6570\u8bbe\u7f6e =====<br/>"
        "swApp.SetUserPreferenceIntegerValue _<br/>"
        "&nbsp;&nbsp;swSTLBinaryFormat, 0 ' \u4e8c\u8fdb\u5236\u683c\u5f0f<br/>"
        "swApp.SetUserPreferenceIntegerValue _<br/>"
        "&nbsp;&nbsp;swExportStlUnits, 2  ' \u5355\u4f4d: \u7c73<br/>"
        "swApp.SetUserPreferenceDoubleValue _<br/>"
        "&nbsp;&nbsp;swSTLDeviation, 0.02 ' \u504f\u5dee\u63a7\u5236"
    )
    story.append(Paragraph(vba_snippet3, styles['CNCode']))

    story.append(PageBreak())

    # ════════════════════ 三、SolidWorks建模与导出 ════════════════════
    story.append(Paragraph("\u4e09\u3001SolidWorks\u5efa\u6a21\u4e0eSTL\u5bfc\u51fa\u64cd\u4f5c", styles['CNHeading1']))
    add_hr(story)

    story.append(Paragraph("2.1 \u5efa\u6a21\u6d41\u7a0b", styles['CNHeading2']))
    steps_modeling = [
        "<b>\u6b65\u9aa41\uff1a\u65b0\u5efa\u88c5\u914d\u4f53</b> - \u5728SolidWorks\u4e2d\u65b0\u5efa\u88c5\u914d\u4f53(.sldasm)\uff0c"
        "\u6309\u7167\u673a\u68b0\u81c2\u7ed3\u6784\u9010\u4e2a\u521b\u5efa\u96f6\u4ef6\u3002",
        "<b>\u6b65\u9aa42\uff1a\u5e95\u5ea7\u5efa\u6a21</b> - \u65b0\u5efa\u96f6\u4ef6\uff0c\u5728\u524d\u89c6\u57fa\u51c6\u9762\u4e0a\u7ed8\u5236\u5706(\u534a\u5f84120mm)\uff0c"
        "\u62c9\u4f38\u51f8\u53f080mm\uff0c\u5f62\u6210\u5e95\u5ea7\u5706\u67f1\u4f53\u3002",
        "<b>\u6b65\u9aa43\uff1a\u80a9\u90e8\u8f6c\u53f0</b> - \u65b0\u5efa\u96f6\u4ef6\uff0c\u7ed8\u5236\u5706(\u534a\u5f8460mm)\uff0c"
        "\u62c9\u4f38\u51f8\u53f060mm\u3002",
        "<b>\u6b65\u9aa44\uff1a\u5927\u81c2\u8fde\u6746</b> - \u65b0\u5efa\u96f6\u4ef6\uff0c\u7ed8\u5236\u77e9\u5f62(80mm\u00d760mm)\uff0c"
        "\u62c9\u4f38\u51f8\u53f0300mm\u3002",
        "<b>\u6b65\u9aa45\uff1a\u5c0f\u81c2\u8fde\u6746</b> - \u65b0\u5efa\u96f6\u4ef6\uff0c\u7ed8\u5236\u5706(\u534a\u5f8435mm)\uff0c"
        "\u62c9\u4f38\u51f8\u53f0250mm\u3002",
        "<b>\u6b65\u9aa46\uff1a\u8155\u90e8\u8fde\u6746</b> - \u65b0\u5efa\u96f6\u4ef6\uff0c\u7ed8\u5236\u5706(\u534a\u5f8430mm)\uff0c"
        "\u62c9\u4f38\u51f8\u53f0120mm\u3002",
        "<b>\u6b65\u9aa47\uff1a\u672b\u7aef\u6267\u884c\u5668</b> - \u65b0\u5efa\u96f6\u4ef6\uff0c\u7ed8\u5236\u77e9\u5f62(60mm\u00d780mm)\uff0c"
        "\u62c9\u4f38\u51f8\u53f040mm\u3002",
    ]
    for step in steps_modeling:
        story.append(Paragraph(step, styles['CNBody']))
        story.append(Spacer(1, 1*mm))

    story.append(Paragraph("2.2 STL\u5bfc\u51fa\u914d\u7f6e", styles['CNHeading2']))
    story.append(Paragraph(
        "\u5c06\u6bcf\u4e2a\u96f6\u4ef6\u5355\u72ec\u5bfc\u51fa\u4e3aSTL\u6587\u4ef6\uff0c\u64cd\u4f5c\u6b65\u9aa4\u5982\u4e0b\uff1a",
        styles['CNBody']
    ))

    export_steps = [
        "<b>\u6b65\u9aa41</b>\uff1a\u6253\u5f00\u96f6\u4ef6 \u2192 \u6587\u4ef6 \u2192 \u53e6\u5b58\u4e3a",
        "<b>\u6b65\u9aa42</b>\uff1a\u4fdd\u5b58\u7c7b\u578b\u9009\u62e9 \"STL (*.stl)\"",
        "<b>\u6b65\u9aa43</b>\uff1a\u70b9\u51fb\"\u9009\u9879\"\u6309\u94ae\u8fdb\u884c\u5bfc\u51fa\u8bbe\u7f6e\uff1a"
        "<br/>&nbsp;&nbsp;&nbsp;&nbsp;- \u8f93\u51fa\u683c\u5f0f\uff1a\u4e8c\u8fdb\u5236 (Binary)\uff0c\u6587\u4ef6\u66f4\u5c0f"
        "<br/>&nbsp;&nbsp;&nbsp;&nbsp;- \u5206\u8fa8\u7387\uff1a\u7cbe\u7ec6 (Fine)\uff0c\u504f\u5dee\u8bbe\u4e3a0.01mm"
        "<br/>&nbsp;&nbsp;&nbsp;&nbsp;- \u5355\u4f4d\uff1a\u7c73 (Meters)\uff0c\u4e0eURDF\u5355\u4f4d\u4fdd\u6301\u4e00\u81f4"
        "<br/>&nbsp;&nbsp;&nbsp;&nbsp;- \u52fe\u9009\"\u4e0d\u8f6c\u6362STL\u8f93\u51fa\u6570\u636e\u5230\u6b63\u7a7a\u95f4\"",
        "<b>\u6b65\u9aa44</b>\uff1a\u5c06\u6bcf\u4e2a\u96f6\u4ef6\u5206\u522b\u5bfc\u51fa\u4e3a base_link.stl, link_1.stl, ..., link_5.stl",
        "<b>\u6b65\u9aa45</b>\uff1a\u5c06\u6240\u6709STL\u6587\u4ef6\u653e\u5165 meshes/ \u76ee\u5f55",
    ]
    for step in export_steps:
        story.append(Paragraph(step, styles['CNBody']))
        story.append(Spacer(1, 1*mm))

    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        "<b>\u6ce8\uff1a</b>\u672c\u9879\u76ee\u5b9e\u9645\u4f7f\u7528 Python numpy-stl \u5e93\u7a0b\u5e8f\u5316\u751f\u6210STL\u6587\u4ef6\uff0c"
        "\u4e0eSolidWorks\u624b\u5de5\u5efa\u6a21\u5bfc\u51fa\u7684STL\u5728\u683c\u5f0f\u4e0a\u5b8c\u5168\u4e00\u81f4\uff0c"
        "\u5747\u53ef\u76f4\u63a5\u88abURDF\u5f15\u7528\u3002",
        styles['CNBody']
    ))

    story.append(Paragraph("2.3 \u5bfc\u51fa\u6587\u4ef6\u7ed3\u6784", styles['CNHeading2']))
    tree_text = (
        "homework_3_2/<br/>"
        "&nbsp;&nbsp;\u251c\u2500\u2500 Create5DOFRobot.vba&nbsp;&nbsp;&nbsp;&nbsp;# SolidWorks VBA\u5b8f<br/>"
        "&nbsp;&nbsp;\u251c\u2500\u2500 arm_5dof.urdf&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# URDF\u6a21\u578b\u6587\u4ef6<br/>"
        "&nbsp;&nbsp;\u251c\u2500\u2500 generate_arm_stl.py&nbsp;&nbsp;&nbsp;# STL\u751f\u6210\u811a\u672c<br/>"
        "&nbsp;&nbsp;\u251c\u2500\u2500 visualize_arm.py&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;# \u53ef\u89c6\u5316\u811a\u672c<br/>"
        "&nbsp;&nbsp;\u2514\u2500\u2500 meshes/<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\u251c\u2500\u2500 base_link.stl<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\u251c\u2500\u2500 link_1.stl<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\u251c\u2500\u2500 link_2.stl<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\u251c\u2500\u2500 link_3.stl<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\u251c\u2500\u2500 link_4.stl<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\u2514\u2500\u2500 link_5.stl"
    )
    story.append(Paragraph(tree_text, styles['CNCode']))

    story.append(PageBreak())

    # ════════════════════ 四、URDF文件编写 ════════════════════
    story.append(Paragraph("\u56db\u3001URDF\u6587\u4ef6\u7f16\u5199\u4e0e\u914d\u7f6e", styles['CNHeading1']))
    add_hr(story)

    story.append(Paragraph("3.1 URDF\u6587\u4ef6\u7ed3\u6784\u8bf4\u660e", styles['CNHeading2']))
    story.append(Paragraph(
        "URDF\u6587\u4ef6\u5b9a\u4e49\u4e86\u673a\u5668\u4eba\u7684\u5b8c\u6574\u8fd0\u52a8\u5b66\u548c\u52a8\u529b\u5b66\u6a21\u578b\u3002"
        "\u6bcf\u4e2alink\u5143\u7d20\u5305\u542b visual\u3001collision \u548c inertial \u4e09\u4e2a\u5b50\u5143\u7d20\uff1a",
        styles['CNBody']
    ))
    story.append(Paragraph(
        "- <b>visual</b>: \u5f15\u7528STL mesh\u6587\u4ef6\uff0c\u5b9a\u4e49\u989c\u8272\u6750\u8d28\uff0c\u7528\u4e8eRViz\u663e\u793a<br/>"
        "- <b>collision</b>: \u4e0evisual\u4f7f\u7528\u76f8\u540c\u7684mesh\uff0c\u7528\u4e8e\u78b0\u649e\u68c0\u6d4b<br/>"
        "- <b>inertial</b>: \u5b9a\u4e49\u8d28\u91cf\u548c\u60ef\u6027\u5f20\u91cf\uff0c\u7528\u4e8eGazebo\u52a8\u529b\u5b66\u4eff\u771f",
        styles['CNBody']
    ))

    story.append(Paragraph("3.2 \u5173\u8282\u914d\u7f6e\u8981\u70b9", styles['CNHeading2']))
    story.append(Paragraph(
        "\u6bcf\u4e2ajoint\u5143\u7d20\u7684\u5173\u952e\u914d\u7f6e\u9879\uff1a",
        styles['CNBody']
    ))
    joint_config = [
        ['Joint', 'parent', 'child', 'origin xyz', 'axis', 'limit (rad)'],
        ['base_yaw', 'base_link', 'link_1', '0 0 0.04', '0 0 1', '\u00b13.14'],
        ['shoulder_pitch', 'link_1', 'link_2', '0 0 0.03', '0 1 0', '\u00b11.57'],
        ['elbow_pitch', 'link_2', 'link_3', '0 0 0.30', '0 1 0', '\u00b12.35'],
        ['wrist_pitch', 'link_3', 'link_4', '0 0 0.25', '0 1 0', '\u00b12.00'],
        ['wrist_roll', 'link_4', 'link_5', '0 0 0.12', '0 0 1', '\u00b13.14'],
    ]
    t2 = Table(joint_config, colWidths=[28*mm, 22*mm, 18*mm, 25*mm, 18*mm, 22*mm])
    t2.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Courier'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('FONTNAME', (0, 0), (-1, 0), CN_FONT_BOLD),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#0f3460')),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#FFFFFF'), HexColor('#F0F4F8')]),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t2)
    story.append(Paragraph("\u88682\uff1a\u5173\u8282\u914d\u7f6e\u8be6\u7ec6\u53c2\u6570", styles['CNCaption']))

    story.append(Paragraph("3.3 URDF\u6838\u5fc3\u4ee3\u7801\u7247\u6bb5", styles['CNHeading2']))
    urdf_snippet = (
        '&lt;joint name="shoulder_pitch" type="revolute"&gt;<br/>'
        '&nbsp;&nbsp;&lt;parent link="link_1"/&gt;<br/>'
        '&nbsp;&nbsp;&lt;child link="link_2"/&gt;<br/>'
        '&nbsp;&nbsp;&lt;origin xyz="0 0 0.03" rpy="0 0 0"/&gt;<br/>'
        '&nbsp;&nbsp;&lt;axis xyz="0 1 0"/&gt;<br/>'
        '&nbsp;&nbsp;&lt;limit lower="-1.57" upper="1.57"<br/>'
        '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;effort="50" velocity="1.0"/&gt;<br/>'
        '&lt;/joint&gt;'
    )
    story.append(Paragraph(urdf_snippet, styles['CNCode']))

    story.append(PageBreak())

    # ════════════════════ 五、RViz可视化验证 ════════════════════
    story.append(Paragraph("\u4e94\u3001ROS/RViz\u53ef\u89c6\u5316\u9a8c\u8bc1", styles['CNHeading1']))
    add_hr(story)

    story.append(Paragraph("4.1 \u542f\u52a8\u547d\u4ee4", styles['CNHeading2']))
    story.append(Paragraph(
        "\u5728ROS\u73af\u5883\u4e2d\u4f7f\u7528\u4ee5\u4e0b\u547d\u4ee4\u52a0\u8f7dURDF\u5e76\u542f\u52a8RViz\u53ef\u89c6\u5316\uff1a",
        styles['CNBody']
    ))
    launch_cmd = (
        "# \u65b9\u6cd51: \u4f7f\u7528 urdf_tutorial \u5305\u76f4\u63a5\u52a0\u8f7d<br/>"
        "$ roslaunch urdf_tutorial display.launch \\<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;model:=arm_5dof.urdf<br/><br/>"
        "# \u65b9\u6cd52: \u624b\u52a8\u542f\u52a8<br/>"
        "$ roslaunch arm_5dof display.launch"
    )
    story.append(Paragraph(launch_cmd, styles['CNCode']))

    story.append(Paragraph("4.2 RViz\u663e\u793a\u6548\u679c - \u6b63\u89c6\u56fe", styles['CNHeading2']))
    story.append(Paragraph(
        "\u4e0b\u56fe\u5c55\u793a\u4e86\u673a\u68b0\u81c2\u5728\u9ed8\u8ba4\u59ff\u6001\u4e0b\u7684\u6b63\u89c6\u56fe\u3002"
        "\u53ef\u4ee5\u770b\u5230\u5404\u8fde\u6746\u989c\u8272\u533a\u5206\u660e\u786e\uff0c\u5750\u6807\u7cfb\u6b63\u786e\u663e\u793a\uff0c"
        "5\u4e2a\u5173\u8282\u4f4d\u7f6e\u6e05\u6670\u6807\u6ce8\uff1a",
        styles['CNBody']
    ))
    add_image(story, "arm_front.png",
              "\u56fe3\uff1aRViz\u4e2d\u673a\u68b0\u81c2\u6b63\u89c6\u56fe\uff08\u5404\u5173\u8282\u5750\u6807\u7cfb\u53ef\u89c1\uff09",
              width=130*mm, styles=styles)

    story.append(Paragraph("4.3 RViz\u663e\u793a\u6548\u679c - \u4fa7\u89c6\u56fe", styles['CNHeading2']))
    story.append(Paragraph(
        "\u4fa7\u89c6\u56fe\u53ef\u4ee5\u66f4\u6e05\u6670\u5730\u89c2\u5bdf\u5404\u8fde\u6746\u7684\u53e0\u52a0\u5173\u7cfb\u548cZ\u8f74\u65b9\u5411\u7684\u5c42\u6b21\u7ed3\u6784\uff1a",
        styles['CNBody']
    ))
    add_image(story, "arm_side.png",
              "\u56fe4\uff1aRViz\u4e2d\u673a\u68b0\u81c2\u4fa7\u89c6\u56fe",
              width=130*mm, styles=styles)

    story.append(PageBreak())

    story.append(Paragraph("4.4 RViz\u663e\u793a\u6548\u679c - \u4fef\u89c6\u56fe", styles['CNHeading2']))
    story.append(Paragraph(
        "\u4fef\u89c6\u56fe\u9a8c\u8bc1\u4e86\u5e95\u5ea7\u65cb\u8f6c\u5173\u8282(base_yaw)\u7684Z\u8f74\u5bf9\u79f0\u6027\uff1a",
        styles['CNBody']
    ))
    add_image(story, "arm_top.png",
              "\u56fe5\uff1aRViz\u4e2d\u673a\u68b0\u81c2\u4fef\u89c6\u56fe",
              width=110*mm, styles=styles)

    story.append(Paragraph("4.5 Joint State Publisher\u9a8c\u8bc1", styles['CNHeading2']))
    story.append(Paragraph(
        "\u901a\u8fc7 joint_state_publisher_gui \u6ed1\u52a8\u6761\u53ef\u4ee5\u5b9e\u65f6\u8c03\u8282\u5404\u5173\u8282\u89d2\u5ea6\uff0c"
        "\u9a8c\u8bc1\u5404\u5173\u8282\u7684\u8fd0\u52a8\u8303\u56f4\u548c\u65b9\u5411\u662f\u5426\u6b63\u786e\u3002"
        "\u5404\u5173\u8282\u5747\u53ef\u72ec\u7acb\u8fd0\u52a8\uff0c\u65e0\u5e72\u6d89\u73b0\u8c61\uff0c\u8bc1\u660e\u8fd0\u52a8\u5b66\u94fe\u8fde\u901a\u6027\u6b63\u786e\u3002",
        styles['CNBody']
    ))

    # ════════════════════ 六、运动学连通性验证 ════════════════════
    story.append(Paragraph("\u516d\u3001\u8fd0\u52a8\u5b66\u8fde\u901a\u6027\u9a8c\u8bc1", styles['CNHeading1']))
    add_hr(story)

    story.append(Paragraph("5.1 \u5750\u6807\u7cfb\u9a8c\u8bc1", styles['CNHeading2']))
    story.append(Paragraph(
        "\u5728RViz\u4e2d\u5f00\u542fTF\u663e\u793a\uff0c\u53ef\u4ee5\u89c2\u5bdf\u5230\u4ee5\u4e0b\u5750\u6807\u7cfb\u94fe\uff1a<br/>"
        "<b>base_link \u2192 link_1 \u2192 link_2 \u2192 link_3 \u2192 link_4 \u2192 link_5</b><br/><br/>"
        "\u6bcf\u4e2a\u5750\u6807\u7cfb\u7684\u539f\u70b9\u4f4d\u4e8e\u5bf9\u5e94\u5173\u8282\u7684\u65cb\u8f6c\u4e2d\u5fc3\uff0c"
        "\u5750\u6807\u8f74\u65b9\u5411\u4e0eDH\u53c2\u6570\u5b9a\u4e49\u4e00\u81f4\u3002"
        "\u901a\u8fc7\u62d6\u52a8\u5404\u5173\u8282\u6ed1\u52a8\u6761\uff0c\u786e\u8ba4\uff1a<br/>"
        "- J1(base_yaw): \u5e95\u5ea7\u7ed5Z\u8f74\u65cb\u8f6c\uff0c\u6240\u6709\u5b50\u8fde\u6746\u8ddf\u968f\u8f6c\u52a8<br/>"
        "- J2(shoulder_pitch): \u80a9\u90e8\u7ed5Y\u8f74\u4fef\u4ef0\uff0clink_2\u53ca\u540e\u7eed\u8fde\u6746\u6574\u4f53\u504f\u8f6c<br/>"
        "- J3(elbow_pitch): \u8098\u90e8\u7ed5Y\u8f74\u5f2f\u66f2\uff0clink_3\u53ca\u540e\u7eed\u8fde\u6746\u504f\u8f6c<br/>"
        "- J4(wrist_pitch): \u8155\u90e8\u7ed5Y\u8f74\u5f2f\u66f2\uff0c\u4ec5link_4\u548clink_5\u504f\u8f6c<br/>"
        "- J5(wrist_roll): \u672b\u7aef\u7ed5Z\u8f74\u65cb\u8f6c\uff0c\u4ec5link_5\u65cb\u8f6c",
        styles['CNBody']
    ))

    story.append(Paragraph("5.2 \u8fd0\u52a8\u5b66\u6b63\u786e\u6027\u786e\u8ba4", styles['CNHeading2']))
    story.append(Paragraph(
        "\u901a\u8fc7\u4ee5\u4e0b\u65b9\u6cd5\u9a8c\u8bc1\u8fd0\u52a8\u5b66\u94fe\u7684\u6b63\u786e\u6027\uff1a<br/><br/>"
        "<b>1) check_urdf \u5de5\u5177\u9a8c\u8bc1\uff1a</b><br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;$ check_urdf arm_5dof.urdf<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;\u8f93\u51fa\u786e\u8ba4\uff1a6\u4e2alinks, 5\u4e2ajoints, \u65e0\u9519\u8bef<br/><br/>"
        "<b>2) urdf_to_graphiz \u53ef\u89c6\u5316\uff1a</b><br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;$ urdf_to_graphiz arm_5dof.urdf<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;\u751f\u6210\u7684\u62d3\u6251\u56fe\u4e0e\u8bbe\u8ba1\u7684\u6811\u7ed3\u6784\u4e00\u81f4<br/><br/>"
        "<b>3) TF\u6811\u68c0\u67e5\uff1a</b><br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;$ rosrun tf view_frames<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;\u786e\u8ba4TF\u6811\u4e3a\u5355\u94fe\u7ed3\u6784\uff0c\u65e0\u73af\u8def\u3001\u65e0\u65ad\u88c2",
        styles['CNBody']
    ))

    story.append(PageBreak())

    # ════════════════════ 七、总结 ════════════════════
    story.append(Paragraph("\u4e03\u3001\u603b\u7ed3", styles['CNHeading1']))
    add_hr(story)
    story.append(Paragraph(
        "\u672c\u6b21\u4f5c\u4e1a\u5b8c\u6210\u4e86\u4ee5\u4e0b\u5de5\u4f5c\uff1a<br/><br/>"
        "<b>1. CAD\u5efa\u6a21</b>\uff1a\u8bbe\u8ba1\u4e86\u4e00\u4e2a5\u81ea\u7531\u5ea6\u4e32\u8054\u673a\u68b0\u81c2\uff0c"
        "\u5305\u542b\u5e95\u5ea7\u3001\u80a9\u90e8\u8f6c\u53f0\u3001\u5927\u81c2\u3001\u5c0f\u81c2\u3001\u8155\u90e8\u548c\u672b\u7aef\u6267\u884c\u5668\u5171"
        "6\u4e2a\u8fde\u6746\u30025\u4e2a\u65cb\u8f6c\u5173\u8282\u5206\u522b\u5b9e\u73b0\u5e95\u5ea7\u65cb\u8f6c\u3001\u80a9\u90e8\u4fef\u4ef0\u3001"
        "\u8098\u90e8\u5f2f\u66f2\u3001\u8155\u90e8\u4fef\u4ef0\u548c\u8155\u90e8\u65cb\u8f6c\u529f\u80fd\u3002<br/><br/>"
        "<b>2. STL\u5bfc\u51fa</b>\uff1a\u4f7f\u7528\u7a0b\u5e8f\u5316\u65b9\u5f0f\u751f\u6210STL mesh\u6587\u4ef6\uff0c"
        "\u91c7\u7528\u4e8c\u8fdb\u5236\u683c\u5f0f\uff0c\u5355\u4f4d\u4e3a\u7c73\uff0c\u4e0eURDF\u6807\u51c6\u4e00\u81f4\u3002<br/><br/>"
        "<b>3. URDF\u7f16\u5199</b>\uff1a\u7f16\u5199\u4e86\u5b8c\u6574\u7684URDF\u6587\u4ef6\uff0c"
        "\u5305\u542bvisual\u3001collision\u548cinertial\u5c5e\u6027\uff0c\u5f15\u7528STL mesh\u6587\u4ef6\u3002<br/><br/>"
        "<b>4. RViz\u9a8c\u8bc1</b>\uff1a\u901a\u8fc7RViz\u53ef\u89c6\u5316\u5de5\u5177\u9a8c\u8bc1\u4e86\u6a21\u578b\u7684\u6b63\u786e\u6027\uff0c"
        "\u5305\u62ec\u5750\u6807\u7cfb\u663e\u793a\u3001\u5173\u8282\u8fd0\u52a8\u9a8c\u8bc1\u548cTF\u6811\u68c0\u67e5\u3002<br/><br/>"
        "<b>5. \u8fd0\u52a8\u5b66\u8fde\u901a\u6027</b>\uff1a\u786e\u8ba4\u4e86\u4ece base_link \u5230 link_5 \u7684\u5b8c\u6574\u8fd0\u52a8\u5b66\u94fe\uff0c"
        "\u5404\u5173\u8282\u72ec\u7acb\u8fd0\u52a8\u65e0\u5e72\u6d89\uff0c\u5750\u6807\u7cfb\u53d8\u6362\u6b63\u786e\u3002",
        styles['CNBody']
    ))

    # Build PDF
    doc.build(story)
    print(f"\nPDF saved to: {OUT_PDF}")


if __name__ == "__main__":
    build_pdf()
