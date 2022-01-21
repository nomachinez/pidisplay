"""
Ticker
(c) Steven Babineau - babineau@gmail.com
2022
"""
import pygame
import yfinance
import requests
import time
import json
import threading
import locale


class Ticker(pygame.sprite.DirtySprite):
    """ Ticker """
    def __init__(self, config, helper, canvas):
        pygame.sprite.DirtySprite.__init__(self)

        self.config = config
        self.helper = helper

        self.screen_height = canvas.get_height()
        self.screen_width = canvas.get_width()

        self.tickers = {}
        self.ticker_surfaces = []
        self.timer = -1
        self.tickers_updated = False

        self.pos_x = 0
        self.ticker_buffer = 40

        font_size = 1
        self.ticker_border_size = 1
        margin = 2
        self.font = pygame.font.SysFont(self.config["application_sysfont"], font_size)
        while self.font.size("XXXX")[1] + (self.ticker_border_size+margin)*2 < self.screen_height:
            font_size += 1
            self.font = pygame.font.SysFont(self.config["application_sysfont"], font_size)

        font_size -= 1
        self.font = pygame.font.SysFont(self.config["application_sysfont"], font_size)

        self.helper.log(self.config, "Found a font size of {}".format(font_size))

    def download_tickers(self):
        self.helper.log(self.config, "TICKER TEST MODE: {}".format(self.config["test_mode"]))

        for i in self.config["tickers"]:
            self.download_ticker(i, self.config["test_mode"])

    def update_ticker_surfaces(self):
        self.ticker_surfaces = []
        locale.setlocale(locale.LC_ALL, "")

        for i in self.tickers:
            if len(i) > 0 and ("currentPrice" in self.tickers[i] or "regularMarketPrice" in self.tickers[i]):
                current_price = self.tickers[i]["currentPrice"] \
                    if "currentPrice" in self.tickers[i] else self.tickers[i]["regularMarketPrice"]

                self.helper.log(self.config, "Current price: {} Open Price {}".format(current_price,
                                                                                      self.tickers[i]["open"]))

                if current_price < self.tickers[i]["open"]:
                    fg_color = self.config["down_foreground"]
                    bg_color = self.config["down_background"]
                elif current_price > self.tickers[i]["open"]:
                    fg_color = self.config["up_foreground"]
                    bg_color = self.config["up_background"]
                else:
                    fg_color = self.config["foreground"]
                    bg_color = self.config["background"]

                surf_ticker_text = self.font.render("{} {}".format(self.tickers[i]["symbol"],
                                                                   locale.currency(current_price, grouping=True)),
                                                    True, fg_color)

                surf_ticker = pygame.Surface((self.ticker_buffer + surf_ticker_text.get_width(), self.screen_height))

                surf_ticker.fill(bg_color)

                brighten_amount = 32
                r = bg_color[0] + brighten_amount
                if r > 255:
                    r = 255
                g = bg_color[1] + brighten_amount
                if g > 255:
                    g = 255
                b = bg_color[1] + brighten_amount
                if b > 255:
                    b = 255

                opposite_bg_color = (r, g, b)
                pygame.draw.rect(surf_ticker, opposite_bg_color,
                                 (0, 0, surf_ticker.get_width(), surf_ticker.get_height()),
                                 self.ticker_border_size)

                surf_ticker.blit(surf_ticker_text, (surf_ticker.get_width()/2 - surf_ticker_text.get_width()/2,
                                                    surf_ticker.get_height()/2 - surf_ticker_text.get_height()/2))

                self.ticker_surfaces.append(surf_ticker)

    def update(self, tick, canvas):
        if int(time.time() * 1000) - self.timer > self.config["update_interval"] * 1000 * 60:
            self.download_tickers()
            self.timer = int(time.time() * 1000)

        if self.tickers_updated:
            self.update_ticker_surfaces()
            self.tickers_updated = False

        canvas.fill(self.config["background"])

        reset_width = 0
        for i in self.ticker_surfaces:
            reset_width += i.get_width()

        if self.config["speed"] > 0:
            if self.pos_x <= reset_width*-1:
                self.pos_x = -reset_width - self.pos_x
        elif self.config["speed"] < 0:
            if self.pos_x > reset_width or self.pos_x == 0:
                self.pos_x = -reset_width

        i = 0
        x = self.pos_x
        j = 0
        if len(self.ticker_surfaces) > 0:
            while x < self.screen_width + reset_width:
                canvas.blit(self.ticker_surfaces[i], (x, 0))
                x += self.ticker_surfaces[i].get_width()

                i += 1
                if i >= len(self.ticker_surfaces):
                    i = 0
                j += 1

        self.pos_x -= self.config["speed"]

    def download_ticker(self, ticker, test_mode):
        thread_timer = threading.Thread(target=self.get_ticker_thread, args=([ticker, test_mode]))
        thread_timer.daemon = False
        thread_timer.start()

    def get_ticker_thread(self, ticker, test_mode):
        session = requests.Session()
        session.headers['User-agent'] = 'pidisplay/1.0'

        self.helper.log(self.config, "getting ticker {} (Test Mode:{})".format(ticker, test_mode))
        if test_mode:
            time.sleep(5)

            ticker_results = json.loads('{"zip": "98052-6399", "sector": "Technology", "fullTimeEmployees": 181000, "longBusinessSummary": "Microsoft Corporation develops, licenses, and supports software, services, devices, and solutions worldwide. Its Productivity and Business Processes segment offers Office, Exchange, SharePoint, Microsoft Teams, Office 365 Security and Compliance, and Skype for Business, as well as related Client Access Licenses (CAL); Skype, Outlook.com, OneDrive, and LinkedIn; and Dynamics 365, a set of cloud-based and on-premises business solutions for organizations and enterprise divisions. Its Intelligent Cloud segment licenses SQL, Windows Servers, Visual Studio, System Center, and related CALs; GitHub that provides a collaboration platform and code hosting service for developers; and Azure, a cloud platform. It also offers support services and Microsoft consulting services to assist customers in developing, deploying, and managing Microsoft server and desktop solutions; and training and certification on Microsoft products. Its More Personal Computing segment provides Windows original equipment manufacturer (OEM) licensing and other non-volume licensing of the Windows operating system; Windows Commercial, such as volume licensing of the Windows operating system, Windows cloud services, and other Windows commercial offerings; patent licensing; Windows Internet of Things; and MSN advertising. It also offers Surface, PC accessories, PCs, tablets, gaming and entertainment consoles, and other devices; Gaming, including Xbox hardware, and Xbox content and services; video games and third-party video game royalties; and Search, including Bing and Microsoft advertising. It sells its products through OEMs, distributors, and resellers; and directly through digital marketplaces, online stores, and retail stores. It has collaborations with Dynatrace, Inc., Morgan Stanley, Micro Focus, WPP plc, ACI Worldwide, Inc., and iCIMS, Inc., as well as strategic relationships with Avaya Holdings Corp. and wejo Limited. Microsoft Corporation was founded in 1975 and is based in Redmond, Washington.", "city": "Redmond", "phone": "425 882 8080", "state": "WA", "country": "United States", "companyOfficers": [], "website": "https://www.microsoft.com", "maxAge": 1, "address1": "One Microsoft Way", "industry": "Software\\u2014Infrastructure", "ebitdaMargins": 0.48648998, "profitMargins": 0.38515, "grossMargins": 0.68864995, "operatingCashflow": 81945001984, "revenueGrowth": 0.22, "operatingMargins": 0.42143002, "ebitda": 85745000448, "targetLowPrice": 299.93, "recommendationKey": "buy", "grossProfits": 115856000000, "freeCashflow": 49819750400, "targetMedianPrice": 370, "currentPrice": 302.65, "earningsGrowth": 0.489, "currentRatio": 2.165, "returnOnAssets": 0.14589, "numberOfAnalystOpinions": 43, "targetMeanPrice": 371.23, "debtToEquity": 51.938, "returnOnEquity": 0.49303, "targetHighPrice": 425, "totalCash": 130584002560, "totalDebt": 78934999040, "totalRevenue": 176250994688, "totalCashPerShare": 17.393, "financialCurrency": "USD", "revenuePerShare": 23.395, "quickRatio": 1.961, "recommendationMean": 1.7, "exchange": "NMS", "shortName": "Microsoft Corporation", "longName": "Microsoft Corporation", "exchangeTimezoneName": "America/New_York", "exchangeTimezoneShortName": "EST", "isEsgPopulated": false, "gmtOffSetMilliseconds": "-18000000", "quoteType": "EQUITY", "symbol": "MSFT", "messageBoardId": "finmb_21835", "market": "us_market", "annualHoldingsTurnover": null, "enterpriseToRevenue": 12.599, "beta3Year": null, "enterpriseToEbitda": 25.898, "52WeekChange": 0.38272262, "morningStarRiskRating": null, "forwardEps": 10.55, "revenueQuarterlyGrowth": null, "sharesOutstanding": 7507979776, "fundInceptionDate": null, "annualReportExpenseRatio": null, "totalAssets": null, "bookValue": 20.242, "sharesShort": 39382126, "sharesPercentSharesOut": 0.0052, "fundFamily": null, "lastFiscalYearEnd": 1625011200, "heldPercentInstitutions": 0.71826, "netIncomeToCommon": 67882999808, "trailingEps": 8.939, "lastDividendValue": 0.62, "SandP52WeekChange": 0.21054816, "priceToBook": 14.951585, "heldPercentInsiders": 0.00062, "nextFiscalYearEnd": 1688083200, "yield": null, "mostRecentQuarter": 1632960000, "shortRatio": 1.35, "sharesShortPreviousMonthDate": 1638230400, "floatShares": 7501148182, "beta": 0.862138, "enterpriseValue": 2220641222656, "priceHint": 2, "threeYearAverageReturn": null, "lastSplitDate": 1045526400, "lastSplitFactor": "2:1", "legalType": null, "lastDividendDate": 1637107200, "morningStarOverallRating": null, "earningsQuarterlyGrowth": 0.476, "priceToSalesTrailing12Months": 12.892354, "dateShortInterest": 1640908800, "pegRatio": 2.04, "ytdReturn": null, "forwardPE": 28.687202, "lastCapGain": null, "shortPercentOfFloat": 0.0052, "sharesShortPriorMonth": 40876626, "impliedSharesOutstanding": null, "category": null, "fiveYearAverageReturn": null, "previousClose": 310.2, "regularMarketOpen": 304.07, "twoHundredDayAverage": 291.55994, "trailingAnnualDividendYield": 0.007414571, "payoutRatio": 0.25059998, "volume24Hr": null, "regularMarketDayHigh": 309.775, "navPrice": null, "averageDailyVolume10Day": 36715180, "regularMarketPreviousClose": 310.2, "fiftyDayAverage": 330.9828, "trailingAnnualDividendRate": 2.3, "open": 304.07, "toCurrency": null, "averageVolume10days": 36715180, "expireDate": null, "algorithm": null, "dividendRate": 2.48, "exDividendDate": 1644969600, "circulatingSupply": null, "startDate": null, "regularMarketDayLow": 301.79, "currency": "USD", "trailingPE": 33.857254, "regularMarketVolume": 42434112, "lastMarket": null, "maxSupply": null, "openInterest": null, "marketCap": 2272290144256, "volumeAllCurrencies": null, "strikePrice": null, "averageVolume": 28079319, "dayLow": 301.79, "ask": 301.9, "askSize": 800, "volume": 42434112, "fiftyTwoWeekHigh": 349.67, "fromCurrency": null, "fiveYearAvgDividendYield": 1.39, "fiftyTwoWeekLow": 217.29, "bid": 301.78, "tradeable": false, "dividendYield": 0.0082, "bidSize": 900, "dayHigh": 309.775, "regularMarketPrice": 302.65, "preMarketPrice": 304.28, "logo_url": "https://logo.clearbit.com/microsoft.com", "trailingPegRatio": 2.9113}')
            results = {ticker: ticker_results}
        else:
            results = {ticker: yfinance.Ticker(ticker, session=session).info}

        lock = threading.Lock()
        lock.acquire()
        self.tickers.update(results)
        self.tickers_updated = True
        self.helper.log(self.config, "done getting ticker {}".format(ticker))
        lock.release()
