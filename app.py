from flask import Flask, render_template, request

app = Flask(__name__);

@app.route("/")
def index():
    return render_template("index.html")


@app.route('/post', methods=['POST'])
def addRegion():
    print("I got it!")
    stksymbol = (request.form['stksymbol'])
    allotment = (request.form['allotment'])
    iniprice = (request.form['iniprice'])
    sellcmm = (request.form['sellcmm'])
    fnlprice = (request.form['fnlprice'])
    buycmm = (request.form['buycmm'])
    cptlgain = (request.form['cptlgain'])



    proceeds = int(allotment) * int(fnlprice)
    ttlshareprice = (int(allotment) * int(iniprice))
    cmm = int(sellcmm) + int(buycmm)

    gain = float(proceeds) - float(ttlshareprice) - float(cmm)

    tocg = float(cptlgain) * float(gain)

    #tocg = ((int(cptlgain)/100) * (int(proceeds) - int(ttlshareprice))) + cmm
    cost = (float(tocg)/100) + cmm + ttlshareprice



    inter = proceeds - ttlshareprice + int(sellcmm) + int(buycmm)
    netprft = proceeds - cost
    roi = netprft*100 / cost

    brkeven = (float(proceeds) - float(inter)) / float(allotment)

    return render_template("index2.html", stksymbol=stksymbol, proceeds=proceeds, cost=cost, tocg=tocg, ttlshareprice=ttlshareprice, buycmm=buycmm, sellcmm=sellcmm, netprft=netprft, roi=roi, brkeven=brkeven)


if __name__=='__main__':
    app.run(debug=True, port=8080)
