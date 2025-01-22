from pprint import pprint
import os
from dotenv import load_dotenv
from web3._utils.filters import AsyncFilter
from web3.types import FilterParams, LogReceipt, LogsSubscriptionArg, FormattedEthSubscriptionResponse

from web3 import AsyncWeb3

MAINNET_ETH_USDT_1PP_POOL = '0xc7bBeC68d12a0d1830360F8Ec58fA599bA1b0e9b'
BASE_ETH_USDC_1PP_POOL = '0xb4CB800910B228ED3d0834cF79D697127BBB00e5'
AERODOME_ETH_USDC_1PP_POOL = '0xb2cc224c1c9feE385f8ad6a55b4d94E92359DC59'
QUICKSWAP_ETH_USDC_POOL = '0x55CAaBB0d2b704FD0eF8192A7E35D8837e678207'

def sqrtX96ToPrice(sqrtx96, decimals0, decimals1, token0IsInput = True):
    ratio = (sqrtx96 / (2 ** 96)) ** 2
    shiftDecimals = 10 ** (decimals0 - decimals1)

    price = ratio * shiftDecimals
    if not token0IsInput:
        price = 1 / price

    return price


async def main():

    load_dotenv('src/evm/.env')

    # PROVIDER_WS_RPC = os.getenv('ETH_MAINNET_WS')
    # PROVIDER_WS_RPC = os.getenv('BASE_MAINNET_WS')
    PROVIDER_WS_RPC = os.getenv('POLYGON_MAINNET_WS')

    w3 = AsyncWeb3(AsyncWeb3.WebSocketProvider(PROVIDER_WS_RPC))

    try:
        await w3.provider.connect()
        print(await w3.is_connected())


        # pool_address = AsyncWeb3.to_checksum_address(MAINNET_ETH_USDT_1PP_POOL)  # Example: USDC/ETH Pool
        # pool_address = AsyncWeb3.to_checksum_address(AERODOME_ETH_USDC_1PP_POOL)  # Example: USDC/ETH Pool
        pool_address = AsyncWeb3.to_checksum_address(QUICKSWAP_ETH_USDC_POOL)  # Example: USDC/ETH Pool

        pool_abi = [
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "internalType": "address", "name": "sender", "type": "address"},
                    {"indexed": True, "internalType": "address", "name": "recipient", "type": "address"},
                    {"indexed": False, "internalType": "int256", "name": "amount0", "type": "int256"},
                    {"indexed": False, "internalType": "int256", "name": "amount1", "type": "int256"},
                    {"indexed": False, "internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
                    {"indexed": False, "internalType": "uint128", "name": "liquidity", "type": "uint128"},
                    {"indexed": False, "internalType": "int24", "name": "tick", "type": "int24"}],
                "name": "Swap", "type": "event"
            }
        ]

        # Create contract instance
        pool_contract = w3.eth.contract(address=pool_address, abi=pool_abi)

        # Get event signature hash
        swap_event_signature = w3.keccak(text="Swap(address,address,int256,int256,uint160,uint128,int24)")

        filter_params = {
            "address": pool_address,
            "topics": [swap_event_signature]
        }

        async def read_subs():
            sub_id = await w3.eth.subscribe("logs", LogsSubscriptionArg(**filter_params))
            print(sub_id)

            async for payload in w3.socket.process_subscriptions():
                res: FormattedEthSubscriptionResponse = payload
                result: LogReceipt = res["result"]
                print("New Swap event:")
                event_data = pool_contract.events.Swap().process_log(result)
                swap_details = dict(**event_data['args'])
                # TODO: Fix the price calculation based on whether token0 is input or not
                # TODO: Read token decimals from their contract
                eth_is_input_0 = abs(swap_details['amount0']) > abs(swap_details['amount1'])
                eth_amount = swap_details['amount0'] if eth_is_input_0 else swap_details['amount1']
                bought_eth = eth_amount > 0
                if bought_eth:
                    swap_details['price'] = sqrtX96ToPrice(swap_details['sqrtPriceX96'], 18, 6, True)
                else:
                    swap_details['price'] = sqrtX96ToPrice(swap_details['sqrtPriceX96'], 6, 18, False)
                pprint(swap_details)

        await read_subs()

    finally:
        await w3.provider.disconnect()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())


