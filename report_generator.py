from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter



def create_report(
    filename,
    machine_info,
    summary_data,
    metadata,
    twf_image=None,
    fft_image=None,
    history=None
):

    doc = SimpleDocTemplate(
        filename,
        pagesize=letter
    )

    styles = getSampleStyleSheet()

    content = []


    # Title

    content.append(
        Paragraph(
            "Quadrant2 Vibration Dashboard Report",
            styles["Title"]
        )
    )

    content.append(
        Spacer(1,20)
    )


    # Machine Information

    content.append(
        Paragraph(
            "Machine Information",
            styles["Heading2"]
        )
    )


    table_data = [
        [k,str(v)]
        for k,v in machine_info.items()
    ]


    table = Table(table_data)

    table.setStyle(
        TableStyle([
            ('GRID',(0,0),(-1,-1),0.5,None)
        ])
    )


    content.append(table)


    content.append(
        Spacer(1,20)
    )


    # Summary

    content.append(
        Paragraph(
            "Measurement Summary",
            styles["Heading2"]
        )
    )


    summary_table = Table(
        [
            [k,str(v)]
            for k,v in summary_data.items()
        ]
    )


    summary_table.setStyle(
        TableStyle([
            ('GRID',(0,0),(-1,-1),0.5,None)
        ])
    )


    content.append(summary_table)


    content.append(
        Spacer(1,20)
    )


    # Metadata

    content.append(
        Paragraph(
            "Signal Metadata",
            styles["Heading2"]
        )
    )


    meta_table = Table(
        [
            [k,str(v)]
            for k,v in metadata.items()
        ]
    )


    meta_table.setStyle(
        TableStyle([
            ('GRID',(0,0),(-1,-1),0.5,None)
        ])
    )


    content.append(meta_table)



    # TWF image

    if twf_image:

        content.append(
            Spacer(1,20)
        )

        content.append(
            Paragraph(
                "Time Waveform",
                styles["Heading2"]
            )
        )

        content.append(
            Image(
                twf_image,
                width=400,
                height=250
            )
        )


    # FFT image

    if fft_image:

        content.append(
            Spacer(1,20)
        )

        content.append(
            Paragraph(
                "FFT Spectrum",
                styles["Heading2"]
            )
        )

        content.append(
            Image(
                fft_image,
                width=400,
                height=250
            )
        )


    doc.build(content)