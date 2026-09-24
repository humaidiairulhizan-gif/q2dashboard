from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

from reportlab.lib.styles import getSampleStyleSheet



def create_report(
        filename,
        machine_info,
        summary_data
):

    doc = SimpleDocTemplate(filename)

    styles = getSampleStyleSheet()

    content = []


    content.append(
        Paragraph(
            "Quadrant2 Vibration Dashboard Report",
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


    machine_table = []


    for k,v in machine_info.items():

        machine_table.append(
            [
                k,
                str(v)
            ]
        )


    table = Table(machine_table)


    table.setStyle(
        TableStyle(
            [
                ('GRID',(0,0),(-1,-1),0.5,None)
            ]
        )
    )


    content.append(table)


    content.append(
        Spacer(1,20)
    )


    content.append(
        Paragraph(
            "Measurement Summary",
            styles["Heading2"]
        )
    )


    summary_table=[]


    for k,v in summary_data.items():

        summary_table.append(
            [
                k,
                str(v)
            ]
        )


    table2 = Table(summary_table)


    table2.setStyle(
        TableStyle(
            [
                ('GRID',(0,0),(-1,-1),0.5,None)
            ]
        )
    )


    content.append(table2)


    doc.build(content)