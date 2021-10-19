from flask import Flask, request, render_template, jsonify
import json

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    return render_template("render.html")


@app.route("/k", methods=["GET"])
def k():
    return render_template("candlestick.html")


@app.route("/kjson", methods=["GET", "POST"])
def kjson():
    js = json.dumps(
        {'title': {'text': '爬虫状态展示'}, 'legend': {'data': ['订单爬虫', '库存爬虫']},
         'toolbox': {'feature': {'saveAsImage': {}, 'dataZoom': {'yAxisIndex': 'false'}}},
         'grid': {'left': '3%', 'right': '4%', 'bottom': '8%', 'containLabel': 'true'}, 'xAxis': [
            {'type': 'category', 'boundaryGap': 'false',
             'data': ['2019-06-24T16:00:00+08:00', '2019-06-24T16:05:00+08:00', '2019-06-24T16:10:00+08:00',
                      '2019-06-24T16:15:00+08:00', '2019-06-24T16:20:00+08:00', '2019-06-24T16:25:00+08:00',
                      '2019-06-24T16:30:00+08:00', '2019-06-24T16:35:00+08:00']}],
         'yAxis': [{'type': 'value', 'min': 0, 'max': 3}],
         'dataZoom': [{'type': 'inside', 'start': 20, 'end': 100}, {'start': 0, 'end': 100, 'handleSize': '60%'}],
         'series': [{'name': '订单爬虫', 'type': 'line', 'data': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]},
                    {'name': '库存爬虫', 'type': 'line', 'data': [1.5, 1.5, 1.5, 1.5, 1.5, 1.5]}]}

    )
    return js


@app.route("/order", methods=["GET", "POST"])
def order():
    js = json.dumps(
        {'result': [{'name': '状态异常爬虫', 'children': [
            {'name': '万里牛', 'children': [{'name': '订单爬虫', 'value': 1}, {'name': '订单爬虫', 'value': 1}]}]},
                    {'name': '状态正常爬虫', 'children': [
                        {'name': '万里牛', 'children': [{'name': '库存爬虫', 'value': 1}, {'name': '库存爬虫', 'value': 1}]}]}]}

    )
    return js


if __name__ == "__main__":
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True)
