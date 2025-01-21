import os
from pprint import pprint
import asyncio
from typing import List, cast
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment, Finalized
from solana.rpc.websocket_api import SolanaWsClientProtocol, connect
from solders.pubkey import Pubkey
from solders.rpc.config import RpcTransactionLogsFilter, RpcTransactionLogsFilterMentions
from solders.rpc.responses import LogsNotification
from solders.signature import Signature
from solders.transaction_status import UiCompiledInstruction, UiInstruction, UiParsedInstruction, UiPartiallyDecodedInstruction, UiTransaction

from dotenv import load_dotenv

RAYDIUM_PUBLIC_KEY = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8";

def is_radium_swap(instruction: UiPartiallyDecodedInstruction):
    public_key_matches = instruction.program_id == Pubkey.from_string(RAYDIUM_PUBLIC_KEY)
    length_match = len(instruction.accounts) == 17
    return public_key_matches and length_match


async def fetch_and_parse_transaction(https_client: AsyncClient, txId: Signature):
    print(txId)
    reciept = await https_client.get_transaction(txId, max_supported_transaction_version=0)

    # TODO: Add parsing

async def main():

    load_dotenv('src/svm/.env')

    HTTPS_RPC = os.getenv("QUICKNODE_HTTPS_RPC")
    WS_RPC = os.getenv("QUICKNODE_WS_RPC")

    print(HTTPS_RPC)
    print(WS_RPC)

    # https_client = AsyncClient(PUBLIC_RPC)
    https_client = AsyncClient(HTTPS_RPC)

    print(await https_client.is_connected())


    # Alternatively, use the client as an infinite asynchronous iterator:
    try:
        async with connect(WS_RPC) as websocket:
            await websocket.logs_subscribe(
                RpcTransactionLogsFilterMentions(pubkey=Pubkey.from_string(RAYDIUM_PUBLIC_KEY)), 
                    commitment=Finalized,
                )
            first_resp = await websocket.recv()
            subscription_id = first_resp[0].result
            print(subscription_id)
            async for msg in websocket:
                notifications: List[LogsNotification] = msg
                # print(len(notifications))
                res = notifications[0].result
                txId = res.value.signature
                logs = res.value.logs
                if 'swap' in " ".join(logs):
                    # print(txId)
                    await fetch_and_parse_transaction(https_client, txId)
                # if 'swap' in logs:
                # pprint(logs)
            print("Unsubscribing")
            await websocket.logs_unsubscribe(subscription_id)

    finally:
        await https_client.close()

asyncio.run(main())
