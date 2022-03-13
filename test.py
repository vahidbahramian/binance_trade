import asyncio
import datetime

from kucoin.client import Client
from kucoin.exceptions import KucoinAPIException
from kucoin.asyncio import KucoinSocketManager

api_key = '6113b0391c8cc90006ace4e5'
api_secret = 'f2a6f82e-922c-4c87-a67b-c9ed02ecd5ac'
api_passphrase = 'V@hid1370'


async def main():
    global loop
    client = Client(api_key, api_secret, api_passphrase)
    # currency_pair = ['BTC-USDT', 'ETH-USDT', 'XRP-USDT', 'TRX-USDT', 'ADA-USDT', 'LTC-USDT', 'ETH-BTC', 'XRP-BTC',
    #                  'TRX-BTC', 'ADA-BTC', 'LTC-BTC']
    currency_pair = ['BTC-USDT']
    count = 0
    # callback function that receives messages from the socket
    async def handle_evt(c, i, msg):
        print(c, i, msg)
    #     if msg['topic'] == '/market/ticker:ETH-USDT':
    #         print(f'got ETH-USDT tick:{msg["data"]}')
    #
    #     elif msg['topic'] == '/market/snapshot:BTC':
    #         print(f'got BTC market snapshot:{msg["data"]}')
    #
    #     elif msg['topic'] == '/market/snapshot:KCS-BTC':
    #         print(f'got KCS-BTC symbol snapshot:{msg["data"]}')
    #
    #     elif msg['topic'] == '/market/ticker:all':
    #         print(f'got all market snapshot:{msg["data"]}')
    #
    #     elif msg['topic'] == '/account/balance':
    #         print(f'got account balance:{msg["data"]}')
    #
    #     elif msg['topic'] == '/market/level2:KCS-BTC':
    #         print(f'got L2 msg:{msg["data"]}')
    #
    #     elif msg['topic'] == '/market/match:BTC-USDT':
    #         print(f'got market match msg:{msg["data"]}')
    #
    #     elif msg['subject'] == 'trade.candles.update':
    #         time = datetime.datetime.utcfromtimestamp(int(msg['data']['candles'][0]))
    #         klines = client.get_kline_data(msg['data']['symbol'], '1hour',
    #                                        int(time.timestamp()) + time.astimezone().utcoffset().seconds - 3600,
    #                                        int(time.timestamp()) + time.astimezone().utcoffset().seconds)
    #         # if msg['data']['symbol'] == 'BTC-USDT':
    #         print(msg['data']['symbol'])
    #     elif msg['topic'] == '/market/level3:BTC-USDT':
    #         if msg['subject'] == 'trade.l3received':
    #             if msg['data']['type'] == 'activated':
    #                 # must be logged into see these messages
    #                 print(f"L3 your order activated: {msg['data']}")
    #             else:
    #                 print(f"L3 order received:{msg['data']}")
    #         elif msg['subject'] == 'trade.l3open':
    #             print(f"L3 order open: {msg['data']}")
    #         elif msg['subject'] == 'trade.l3done':
    #             print(f"L3 order done: {msg['data']}")
    #         elif msg['subject'] == 'trade.l3match':
    #             print(f"L3 order matched: {msg['data']}")
    #         elif msg['subject'] == 'trade.l3change':
    #             print(f"L3 order changed: {msg['data']}")
    #
    # client = Client(api_key, api_secret, api_passphrase)
    #
    # ksm = await KucoinSocketManager.create(loop, client, handle_evt)
    #
    # # for private topics such as '/account/balance' pass private=True
    # ksm_private = await KucoinSocketManager.create(loop, client, handle_evt, private=True)
    #
    # # Note: try these one at a time, if all are on you will see a lot of output
    #
    # await ksm.subscribe('/market/candles:' + 'BTC-USDT' + "_" +
    #                          '1min')
    # await ksm.subscribe('/market/candles:' + 'ETH-USDT' + "_" +
    #                          '1min')
    # await ksm.subscribe('/market/candles:' + 'XRP-USDT' + "_" +
    #                          '1min')
    # await ksm.subscribe('/market/candles:' + 'TRX-USDT' + "_" +
    #                          '1min')
    # await ksm.subscribe('/market/candles:' + 'ADA-USDT' + "_" +
    #                          '1min')
    # await ksm.subscribe('/market/candles:' + 'LTC-USDT' + "_" +
    #                          '1min')
    # await ksm.subscribe('/market/candles:' + 'ETH-BTC' + "_" +
    #                          '1min')
    # await ksm.subscribe('/market/candles:' + 'XRP-BTC' + "_" +
    #                          '1min')
    # await ksm.subscribe('/market/candles:' + 'TRX-BTC' + "_" +
    #                          '1min')
    # await ksm.subscribe('/market/candles:' + 'ADA-BTC' + "_" +
    #                          '1min')
    # await ksm.subscribe('/market/candles:' + 'LTC-BTC' + "_" +
    #                          '1min')
    # # ETH-USDT Market Ticker
    # await ksm.subscribe('/market/ticker:ETH-USDT')
    # # BTC Symbol Snapshots
    # await ksm.subscribe('/market/snapshot:BTC')
    # # KCS-BTC Market Snapshots
    # await ksm.subscribe('/market/snapshot:KCS-BTC')
    # # All tickers
    # await ksm.subscribe('/market/ticker:all')
    # # Level 2 Market Data
    # await ksm.subscribe('/market/level2:KCS-BTC')
    # # Market Execution Data
    # await ksm.subscribe('/market/match:BTC-USDT')
    # # Level 3 market data
    # await ksm.subscribe('/market/level3:BTC-USDT')
    # # Account balance - must be authenticated
    # await ksm_private.subscribe('/account/balance')

    while True:
        # print("sleeping to keep loop open")
        for i in currency_pair:
            try:
                klines = client.get_kline_data(i, '1hour', int(datetime.datetime.now().timestamp()) - 7200,
                                               int(datetime.datetime.now().timestamp()))
                count += 1
                await handle_evt(count, i, klines[-1])
                # await asyncio.sleep(0.5, loop=loop)
            except KucoinAPIException as e:
                print(e)


if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())