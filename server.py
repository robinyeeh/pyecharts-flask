# -*- coding:UTF-8 -*-
import logging
import time

import psycopg2

from flask import Flask, render_template

app = Flask(__name__)

database_server_host = '192.168.4.112'
database_server_port = 5432
database_name = 'swiftsight_report_prod'
database_username = 'postgres'
database_password = 'conversant'

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)
handler = logging.FileHandler("log.txt")
# handler = logging.FileHandler("D:\\log.txt")
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

@app.route("/bandwidth")
def bandwidth():
    charts = bandwidth_line()
    return render_template('pyecharts.html',
                           myechart=charts.render_embed(),
                           # host=DEFAULT_HOST,
                           script_list=charts.get_js_dependencies()
                           )


def bandwidth_line():
    from pyecharts import Line

    attr, val = get_bandwidth_data('c1-ex-swe.nixcdn.com', 1528242900000, 1528276200000)

    line = Line("Bandwidth", width=1400, height=600)
    line.add("Bandwidth", attr, val, is_smooth=True, is_label_show=False,
             mark_point=["average", "max", "min"],
             yaxis_formatter=y_label_formatter,
             tooltip_formatter=tooltip_formatter,
             tooltip_axispointer_type="shadow", interval=0)

    return line


def get_bandwidth_data(domain, start, end, interval=None):
    conn = psycopg2.connect(host=database_server_host, port=database_server_port, user=database_username,
                            password=database_password, database=database_name)
    cursor = conn.cursor()

    query_sql = "select spot_time,service_name,sum(throughput) as throughput from cdn_throughput_spot where 1=1 and service_name in ('%s') and spot_time >= %d and spot_time <= %d group by spot_time,service_name order by service_name,spot_time;" % (
        domain, start, end)

    try:
        cursor.execute(query_sql)
        rows = cursor.fetchall()

        spot_times = []
        spot_values = []
        for row in rows:
            spot_times.append(time.strftime("%H:%M", time.localtime(row[0] / 1000)))
            spot_values.append(float(row[2]))

        return spot_times, spot_values
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def y_label_formatter(params):
    units = ["bps", "Kbps", "Mbps", "Gbps", "Tbps", "Pbps", "Ebps", "Zbps", "Ybps", "Bbps", "Nbps", "Dbps", "Cbps",
             "Xbps"];

    i = 0
    while params > 1000.0:
        params = params / 1000.0
        i += 1

    return params + " " + units[i]


def tooltip_formatter(params):
    units = ["bps", "Kbps", "Mbps", "Gbps", "Tbps", "Pbps", "Ebps", "Zbps", "Ybps", "Bbps", "Nbps", "Dbps", "Cbps",
             "Xbps"];

    i = 0
    data = params.data
    while data > 1000.0:
        data = data / 1000.0
        i += 1

    return data.toFixed(2) + " " + units[i]
