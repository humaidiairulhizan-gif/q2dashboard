from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet



def create_report(
    filename,
    info,
    summary
):


    doc = SimpleDocTemplate(
        filename
    )


    styles = getSampleStyleSheet()


    content = []


    content.append(
        Paragraph(
            "Quadrant2 Vibration Monitoring Report",
            styles["Title"]
        )
    )


    content.append(
        Spacer(1,20)
    )


    content.append(
        Paragraph(
            "Machine Information",
            styles["Heading2"]
        )
    )


    for key,value in info.items():

        content.append(
            Paragraph(
                f"{key}: {value}",
                styles["Normal"]
            )
        )


    content.append(
        Spacer(1,20)
    )


    content.append(
        Paragraph(
            "Measurement Summary",
            styles["Heading2"]
        )
    )


    for key,value in summary.items():

        content.append(
            Paragraph(
                f"{key}: {value}",
                styles["Normal"]
            )
        )


    doc.build(content)