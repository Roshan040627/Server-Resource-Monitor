import os
import json
from datetime import datetime, timedelta
from config import LOG_DIR, KEEP_LOG_DAYS, RAM_WARNING_LIMIT
import io
import base64
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt



def shorten(text, max_len=25):
    text = str(text)
    return text if len(text) <= max_len else text[:max_len] + "..."


def rank_class(i):
    if i == 1:
        return "rank-one"
    elif i == 2:
        return "rank-two"
    elif i == 3:
        return "rank-three"
    return ""

def fig_to_base64(fig):
    buffer = io.BytesIO()
    fig.savefig(
        buffer,
        format="png",
        dpi=150,
        bbox_inches="tight",
        facecolor=fig.get_facecolor()
    )
    plt.close(fig)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


def create_ram_pie_chart(data):
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    ax.pie(
        [data["ram_percent"], data["ram_free_percent"]],
        labels=["RAM Used", "RAM Free"],
        autopct="%1.1f%%",
        startangle=90,
        pctdistance=0.72,
        labeldistance=1.08,
        radius=0.88
    )
    ax.set_title(
        "Estimated RAM Usage Overview", 
        fontsize=18,
        fontweight="bold",
        pad=20
    )
    
    ax.set_aspect("equal")

    for spine in ax.spines.values():
        spine.set_visible(False)
    
    plt.tight_layout()
    
    return fig_to_base64(fig)


def create_cpu_pie_chart(data):
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    
    ax.pie(
        [data["cpu_percent"], data["cpu_idle_percent"]],
        labels=["CPU Used", "CPU Idle"],
        autopct="%1.1f%%",
        startangle=90,
        pctdistance=0.72,
        labeldistance=1.08,
        radius=0.88,
    )
    ax.set_title(
        "Estimated CPU Usage Overview", 
        fontsize=18,
        fontweight="bold",
        pad=20
    )

    ax.set_aspect("equal")
    
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    plt.tight_layout()

    return fig_to_base64(fig)

def create_ram_bar_chart(data):
    items = data["top_memory"][:10]
    labels = [
        f"{i}. {shorten(p['program'].replace(chr(92), '/'), 38)}"
        for i, p in enumerate(items, 1)
    ]
    values = [p["memory_mb"] for p in items]

    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor("#eef2f7")
    ax.set_facecolor("#f8fafc")

    fig.text(
        0.5,
        0.96,
        "Top 10 High RAM Usage Processes",
        ha="center",
        va="center",
        fontsize=18,
        fontweight="bold",
        color="#111827"
    )

    y_pos = range(len(labels))
    ax.barh(y_pos, values, color="#64748b")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()

    max_value = max(values) if values else 1
    ax.set_xlim(0, max_value * 1.35)

    for i, value in enumerate(values):
        ax.text(
            value + max_value * 0.02,
            i,
            f"{value:.1f} MB",
            va="center",
            ha="left",
            fontsize=9,
            fontweight="bold"
        )

    ax.grid(axis="x", alpha=0.18)

    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.subplots_adjust(left=0.32, right=0.96, top=0.88, bottom=0.08)

    return fig_to_base64(fig)


def create_cpu_bar_chart(data):
    items = data["top_cpu"][:10]
    labels = [
        f"{i}. {shorten(p['program'].replace(chr(92), '/'), 38)}"
        for i, p in enumerate(items, 1)
    ]
    values = [p["cpu"] for p in items]

    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor("#eef2f7")
    ax.set_facecolor("#f8fafc")

    fig.text(
        0.5,
        0.96,
        "Top 10 High CPU Usage Processes",
        ha="center",
        va="center",
        fontsize=18,
        fontweight="bold",
        color="#111827"
    )

    y_pos = range(len(labels))
    ax.barh(y_pos, values, color="#475569")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()

    max_value = max(values) if values else 1
    ax.set_xlim(0, max_value * 1.35)

    for i, value in enumerate(values):
        ax.text(
            value + max_value * 0.02,
            i,
            f"{value:.1f}%",
            va="center",
            ha="left",
            fontsize=9,
            fontweight="bold"
        )

    ax.grid(axis="x", alpha=0.18)

    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.subplots_adjust(left=0.32, right=0.96, top=0.88, bottom=0.08)

    return fig_to_base64(fig)

def generate_dashboard_html(data):
    if data["ram_percent"] < RAM_WARNING_LIMIT:
        print(f"BLOCKED: RAM below {RAM_WARNING_LIMIT}%, HTML file not created.")
        return None


    memory_labels = json.dumps([
        shorten(p["program"].replace("\\", "/"), 25)
        for p in data["top_memory"]
    ])

    memory_data = json.dumps([p["memory_mb"] for p in data["top_memory"]])

    memory_percentages = json.dumps([
        round((p["memory_mb"] / (data["ram_total_gb"] * 1024)) * 100, 2)
        for p in data["top_memory"]
    ])

    cpu_labels = json.dumps([
        shorten(p["program"].replace("\\", "/"), 25)
        for p in data["top_cpu"]
    ])

    cpu_data = json.dumps([p["cpu"] for p in data["top_cpu"]])

    ram_rows = ""
    for i, p in enumerate(data["top_memory"], start=1):
        ram_percent = round((p["memory_mb"] / (data["ram_total_gb"] * 1024)) * 100, 2)

        ram_rows += f"""
<tr style="background:#ffffff;">
    <td style="
    padding:12px;
    border-bottom:1px solid #e5e7eb;
    font-weight:bold;
    color:#475569;
    text-align:center;
    ">
    {i}
    </td>

    <td style="
    padding:12px;
    border-bottom:1px solid #e5e7eb;
    ">
    {p['pid']}
    </td>

    <td style="
    padding:12px;
    border-bottom:1px solid #e5e7eb;
    ">
    {p['username']}
    </td>

    <td style="
    padding:12px;
    border-bottom:1px solid #e5e7eb;
    font-weight:600;
    line-height:1.5;
    word-break:break-all;
    overflow-wrap:anywhere;
    max-width:420px;
    ">
    {p['program']}
    </td>

    <td style="
    padding:12px;
    border-bottom:1px solid #e5e7eb;
    font-weight:bold;
    color:#64748b;
    ">
    {ram_percent}%
    </td>

    <td style="
    padding:12px;
    border-bottom:1px solid #e5e7eb;
    ">
    {p['memory_mb']}
    </td>

    <td style="
    padding:12px;
    border-bottom:1px solid #e5e7eb;
    ">
        <span style="
        display:inline-block;
        padding:4px 10px;
        border-radius:999px;
        background:#eef2ff;
        color:#4338ca;
        font-size:12px;
        font-weight:bold;
        ">
        {p['status']}
        </span>
    </td>
</tr>
"""

    cpu_rows = ""
    for i, p in enumerate(data["top_cpu"], start=1):
        cpu_rows += f"""
<tr style="background:#ffffff;">
    <td style="
    padding:12px;
    border-bottom:1px solid #e5e7eb;
    font-weight:bold;
    color:#475569;
    text-align:center;
    ">
    {i}
    </td>

    <td style="
    padding:12px;
    border-bottom:1px solid #e5e7eb;
    ">
    {p['pid']}
    </td>

    <td style="
    padding:12px;
    border-bottom:1px solid #e5e7eb;
    ">
    {p['username']}
    </td>

    <td style="
    padding:12px;
    border-bottom:1px solid #e5e7eb;
    font-weight:600;
    line-height:1.5;
    word-break:break-all;
    overflow-wrap:anywhere;
    max-width:420px;
    ">
    {p['program']}
    </td>

    <td style="
    padding:12px;
    border-bottom:1px solid #e5e7eb;
    font-weight:bold;
    color:#475569;
    ">
    {p['cpu']}%
    </td>

    <td style="
    padding:12px;
    border-bottom:1px solid #e5e7eb;
    ">
    {p['memory_mb']}
    </td>

    <td style="
    padding:12px;
    border-bottom:1px solid #e5e7eb;
    ">
        <span style="
        display:inline-block;
        padding:4px 10px;
        border-radius:999px;
        background:#eef2ff;
        color:#4338ca;
        font-size:12px;
        font-weight:bold;
        ">
        {p['status']}
        </span>
    </td>
</tr>
"""

    ram_pie_img = create_ram_pie_chart(data)
    cpu_pie_img = create_cpu_pie_chart(data)
    ram_bar_img = create_ram_bar_chart(data)
    cpu_bar_img = create_cpu_bar_chart(data)

    chart_images = {
        "ram_pie_chart": base64.b64decode(ram_pie_img),
        "cpu_pie_chart": base64.b64decode(cpu_pie_img),
        "ram_bar_chart": base64.b64decode(ram_bar_img),
        "cpu_bar_chart": base64.b64decode(cpu_bar_img)
    }

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Server Process Monitoring Dashboard</title>
    

    <style>
        body {{
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #eef2f7, #f8fafc);
            padding: 30px;
            color: #1f2937;
        }}

        h1 {{
            text-align: center;
            color: #111827;
            margin-bottom: 5px;
        }}

        .warning {{
            background: #fee2e2;
            color: #991b1b;
            padding: 15px;
            border-radius: 12px;
            text-align: center;
            font-weight: bold;
            margin-bottom: 10px;
        }}

        .server-info {{
            background: white;
            padding: 22px 28px;
            border-radius: 16px;
            box-shadow: 0 6px 18px rgba(0,0,0,0.08);
            margin-bottom: 25px;
            border-left: 6px solid #4e79a7;
        }}

        .summary {{
            display: block;
            width: 100%;
            margin-bottom: 30px;
        }}

        .card {{
            background: white;
            padding: 22px;
            border-radius: 16px;
            box-shadow: 0 6px 18px rgba(0,0,0,0.08);
            text-align: center;
            border-top: 5px solid #4e79a7;
            margin-bottom: 18px;
        }}

        .card:nth-child(2) {{
            border-top-color: #59a14f;
        }}

        .card:nth-child(3) {{
            border-top-color: #f28e2b;
        }}

        .card h2 {{
            margin: 0;
            font-size: 34px;
            color: #111827;
            font-weight: bold;
        }}

        .card p {{
            margin-bottom: 0;
            color: #6b7280;
            font-size: 14px;
            letter-spacing: 0.3px;
        }}

        .dashboard {{
            display: block;
            width: 100%;
            margin-bottom: 25px;
        }}

        .chart-box, .table-box {{
            background: white;
            padding: 20px;
            border-radius: 16px;
            box-shadow: 0 6px 18px rgba(0,0,0,0.08);
            width: 100%;
            margin-bottom: 45px;
            box-sizing: border-box;
        }}

        .chart-box canvas {{
            max-height: 250px;
        }}

        .tables-dashboard {{
            display: block;
            width: 100%;
            margin-top: 25px;
        }}

        .ram-table-box {{
            background:linear-gradient(135deg,#f8fafc,#eef2f7);
            border:1px solid #d6dde8;
            border-top:6px solid #64748b;
            border-top:6px solid #64748b;
            box-shadow:0 8px 20px rgba(0,0,0,0.08);
        }}

        .cpu-table-box {{
            background:linear-gradient(135deg,#f8fafc,#eef2f7);
            border:1px solid #d6dde8;
            border-top:6px solid #475569;
            border-radius:16px;
            box-shadow:0 8px 20px rgba(0,0,0,0.08);
        }}

        .table-title {{
            width: 100%;
            margin-bottom: 10px;
        }}

        .table-title h2 {{
            display: inline-block;
            margin: 0;
        }}

        .badge {{
            display: inline-block;
            margin-left: 10px;
            padding: 6px 12px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: bold;
            color: white;
        }}

        .ram-badge {{
            background:#64748b;
            color:white;
        }}

        .cpu-badge {{
            background:#475569;
            color:white;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            border-radius: 12px;
            table-layout: fixed;
        }}

        th, td {{
            padding: 11px;
            border-bottom: 1px solid #e5e7eb;
            text-align: left;
            font-size: 14px;
        }}

        th {{
            background:#e2e8f0;
            color:#334155;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.4px;
        }}

        tr:hover {{
            background: #f9fafb;
        }}

        .rank {{
            font-weight: bold;
            text-align: center;
            border-radius: 8px;
        }}

        .rank-one {{
            color: #dc2626;
            font-weight: bold;
        }}

        .rank-two {{
            color: #ea580c;
            font-weight: bold;
        }}

        .rank-three {{
            color: #ca8a04;
            font-weight: bold;
        }}

        .process-name {{
            font-weight: 600;
            word-break: break-all;
            overflow-wrap: anywhere;
            max-width: 420px;
            whitespace: normal;
            line-height: 1.5;
        }}

        .value-ram {{
            font-weight: bold;
            color: #e15759;
        }}

        .value-cpu {{
            font-weight: bold;
            color: #f28e2b;
        }}

        .status-pill {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 999px;
            background: #eef2ff;
            color: #4338ca;
            font-size: 12px;
            font-weight: bold;
        }}

        @media (max-width: 900px) {{
            .summary,
            .dashboard,
            .tables-dashboard {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>

<body>

<div style="
text-align:center;
padding:20px 0 10px 0;
">
    <h1 style="
    text-align:center;
    color:#111827;
    font-size:32px;
    font-weight:bold;
    margin:0 0 18px 0;
    ">
    Server Process Monitoring Dashboard
    </h1>

    <p style="
    text-align:center;
    font-size:15px;
    color:#374151;
    margin:0 0 22px 0;
    ">
    Generated on {data['generated_at']}
    </p>

    <div style="
    background:#fee2e2;
    color:#991b1b;
    padding:16px;
    border-radius:12px;
    text-align:center;
    font-weight:bold;
    font-size:15px;
    margin:0 0 28px 0;
    ">
    RAM usage reached {data['ram_percent']}%. Configured warning threshold is {RAM_WARNING_LIMIT}%.
    </div>
</div>

<div style="
background:linear-gradient(135deg,#fff5f5,#ffe4e6);
border:2px solid #f3b7c2;
border-top:6px solid #d71920;
border-radius:18px;
padding:28px;
margin-top:0px;
margin-bottom:18px;
box-shadow:0 8px 20px rgba(215,25,32,0.12);
">
    <p style="margin:14px 0; font-size:16px;">
<strong style="color:#d71920;">Hostname:</strong>
{data['hostname']}
</p>

<p style="margin:14px 0; font-size:16px;">
<strong style="color:#d71920;">IP Address:</strong>
{data['ip_address']}
</p>

<p style="margin:14px 0; font-size:16px;">
<strong style="color:#d71920;">Operating System:</strong>
{data['os']}
</p>

</div>

<table style="
width:100%;
border-collapse:separate;
border-spacing:18px;
margin:30px 0;
padding:18px;
background:#eef2f7;
border:1px solid #d1d5db;
border-radius:18px;
">
    <tr>
        <td style="width:33.33%; padding:10px;">
            <div style="
            background:#ffffff;
            border:1px solid #d1d5db;
            border-top:6px solid #4e79a7;
            border-radius:14px;
            padding:25px;
            text-align:center;
            box-shadow:0 8px 20px rgba(0,0,0,0.12);
            ">
                <div style="font-size:36px; font-weight:bold; color:#111827;">{data['total_processes']}</div>
                <div style="font-size:14px; color:#6b7280; margin-top:8px;">Total Processes</div>
            </div>
        </td>

        <td style="width:33.33%; padding:10px;">
            <div style="
            background:#ffffff;
            border:1px solid #d1d5db;
            border-top:6px solid #59a14f;
            border-radius:14px;
            padding:25px;
            text-align:center;
            box-shadow:0 8px 20px rgba(0,0,0,0.12);
            ">
                <div style="font-size:36px; font-weight:bold; color:#111827;">{data['running']}</div>
                <div style="font-size:14px; color:#6b7280; margin-top:8px;">Running Processes</div>
            </div>
        </td>

        <td style="width:33.33%; padding:10px;">
            <div style="
            background:#ffffff;
            border:1px solid #d1d5db;
            border-top:6px solid #f28e2b;
            border-radius:14px;
            padding:25px;
            text-align:center;
            box-shadow:0 8px 20px rgba(0,0,0,0.12);
            ">
                <div style="font-size:36px; font-weight:bold; color:#111827;">{data['sleeping']}</div>
                <div style="font-size:14px; color:#6b7280; margin-top:8px;">Sleeping / Idle Processes</div>
            </div>
        </td>
    </tr>
</table>

<div class="dashboard">
    <div class="chart-box" style="
    text-align:center;
    background:#eef2f7;
    border:1px solid #d6dde8;
    border-radius:18px;
    padding:20px;
    margin-bottom:35px;
    box-shadow:0 8px 20px rgba(0,0,0,0.08);
    ">
        <img src="cid:ram_pie_chart" style="
        width:100%;
        max-width:420px;
        display:block;
        margin:0 auto;
        ">
    </div>

    <div class="chart-box" style="
    text-align:center;
    background:#eef2f7;
    border:1px solid #d6dde8;
    border-radius:18px;
    padding:20px;
    margin-bottom:35px;
    box-shadow:0 8px 20px rgba(0,0,0,0.08);
    ">
        <img src="cid:cpu_pie_chart" style="
        width:100%;
        max-width:420px;
        display:block;
        margin:0 auto;
        ">
    </div>
</div>

<div class="dashboard">
    <div class="chart-box" style="
    text-align:center;
    background:#eef2f7;
    border:1px solid #d6dde8;
    border-radius:18px;
    padding:20px;
    margin-bottom:35px;
    box-shadow:0 8px 20px rgba(0,0,0,0.08);
    ">
        <img src="cid:ram_bar_chart" style="width:100%; display:block; margin:0 auto;">
    </div>

    <div class="chart-box" style="
    text-align:center;
    background:#eef2f7;
    border:1px solid #d6dde8;
    border-radius:18px;
    padding:20px;
    margin-bottom:35px;
    box-shadow:0 8px 20px rgba(0,0,0,0.08);
    ">
        <img src="cid:cpu_bar_chart" style="width:100%; display:block; margin:0 auto;">
    </div>
</div>

<div class="tables-dashboard">
    <div class="table-box ram-table-box">
        <div style="
display:flex;
align-items:center;
gap:12px;
margin-bottom:18px;
">

<h2 style="
margin:0;
font-size:22px;
font-weight:700;
color:#1e293b;
">
Top 10 RAM Usage
</h2>

<span style="
display:inline-block;
background:linear-gradient(135deg,#64748b,#475569);
color:white;
padding:8px 16px;
border-radius:999px;
font-size:13px;
font-weight:bold;
letter-spacing:0.3px;
box-shadow:0 4px 10px rgba(0,0,0,0.12);
">
Highest RAM
</span>

</div>

        <table style="width:100%; border-collapse:collapse; margin-top:15px; background:#f8fafc; border:1px solid #d6dde8;">
    <tr>
        <th style="width:40px; background:#e2e8f0; color:#334155; padding:12px; border-bottom:1px solid #cbd5e1;">#</th>
        <th style="width:70px; background:#e2e8f0; color:#334155; padding:12px; border-bottom:1px solid #cbd5e1;">PID</th>
        <th style="width:120px; background:#e2e8f0; color:#334155; padding:12px; border-bottom:1px solid #cbd5e1;">User</th>
        <th style="background:#e2e8f0; color:#334155; padding:12px; border-bottom:1px solid #cbd5e1;">Process</th>
        <th style="width:80px; background:#e2e8f0; color:#334155; padding:12px; border-bottom:1px solid #cbd5e1;">RAM %</th>
        <th style="width:90px; background:#e2e8f0; color:#334155; padding:12px; border-bottom:1px solid #cbd5e1;">RAM MB</th>
        <th style="width:90px; background:#e2e8f0; color:#334155; padding:12px; border-bottom:1px solid #cbd5e1;">Status</th>
    </tr>
    {ram_rows}
</table>
    </div>

    <div style="
    margin-top:35px;
    "></div>

    <div class="table-box cpu-table-box">
        <div style="
display:flex;
align-items:center;
gap:12px;
margin-bottom:18px;
">

<h2 style="
margin:0;
font-size:22px;
font-weight:700;
color:#1e293b;
">
Top 10 CPU Usage
</h2>

<span style="
display:inline-block;
background:linear-gradient(135deg,#475569,#334155);
color:white;
padding:8px 16px;
border-radius:999px;
font-size:13px;
font-weight:bold;
letter-spacing:0.3px;
box-shadow:0 4px 10px rgba(0,0,0,0.12);
">
Highest CPU
</span>

</div>

        <table style="width:100%; border-collapse:collapse; margin-top:15px; background:#f8fafc; border:1px solid #d6dde8;">
    <tr>
        <th style="width:40px; background:#e2e8f0; color:#334155; padding:12px; border-bottom:1px solid #cbd5e1;">#</th>
        <th style="width:70px; background:#e2e8f0; color:#334155; padding:12px; border-bottom:1px solid #cbd5e1;">PID</th>
        <th style="width:120px; background:#e2e8f0; color:#334155; padding:12px; border-bottom:1px solid #cbd5e1;">User</th>
        <th style="background:#e2e8f0; color:#334155; padding:12px; border-bottom:1px solid #cbd5e1;">Process</th>
        <th style="width:90px; background:#e2e8f0; color:#334155; padding:12px; border-bottom:1px solid #cbd5e1;">CPU %</th>
        <th style="width:80px; background:#e2e8f0; color:#334155; padding:12px; border-bottom:1px solid #cbd5e1;">RAM MB</th>
        <th style="width:90px; background:#e2e8f0; color:#334155; padding:12px; border-bottom:1px solid #cbd5e1;">Status</th>
    </tr>
            {cpu_rows}
        </table>
    </div>
</div>

</body>
</html>
"""

    html_for_download = html.replace("cid:ram_pie_chart", f"data:image/png;base64,{ram_pie_img}")
    html_for_download = html_for_download.replace("cid:cpu_pie_chart", f"data:image/png;base64,{cpu_pie_img}")
    html_for_download = html_for_download.replace("cid:ram_bar_chart", f"data:image/png;base64,{ram_bar_img}")
    html_for_download = html_for_download.replace("cid:cpu_bar_chart", f"data:image/png;base64,{cpu_bar_img}")

    os.makedirs(LOG_DIR, exist_ok=True)

    filename = f"server_dashboard_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.html"
    filepath = os.path.join(LOG_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as file:
        file.write(html_for_download)

    print(f"Dashboard downloaded/saved to: {filepath}")

    return html, chart_images