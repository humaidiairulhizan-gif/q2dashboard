from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image
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


    story=[]



    story.append(
        Paragraph(
            "Quadrant2 Vibration Report",
            styles["Title"]
        )
    )


    story.append(
        Spacer(1,20)
    )


    for key,value in info.items():

        story.append(
            Paragraph(
                f"{key}: {value}",
                styles["Normal"]
            )
        )


    story.append(
        Spacer(1,20)
    )


    story.append(
        Paragraph(
            "Measurement Summary",
            styles["Heading2"]
        )
    )


    for key,value in summary.items():

        story.append(
            Paragraph(
                f"{key}: {value}",
                styles["Normal"]
            )
        )


    doc.build(story)