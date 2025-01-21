const { Connection, PublicKey } = require("@solana/web3.js");
const BufferLayout = require("buffer-layout");
const { u64 } = require("@solana/buffer-layout-utils");
const { ApiPoolInfo, Clmm } = require("@raydium-io/raydium-sdk");
const RAYDIUM_PUBLIC_KEY = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8";

const SESSION_HASH = "QNDEMO" + Math.ceil(Math.random() * 1e9); // Random unique identifier for your session

const raydium = new PublicKey(RAYDIUM_PUBLIC_KEY);
// Replace HTTP_URL & WSS_URL with QuickNode HTTPS and WSS Solana Mainnet endpoint
const connection = new Connection(
    ``,
    {
        wsEndpoint: ``,
        httpHeaders: { "x-session-hash": SESSION_HASH },
    }
);

// Monitor logs
async function main(connection, programAddress) {
    console.log("Monitoring logs for program:", programAddress.toString());
    connection.onLogs(
        programAddress,
        ({ logs, err, signature }) => {
            if (err) return;

            if (logs && logs.some((log) => log.includes("swap"))) {
                // console.log("Signature for 'swap':", signature);
                fetchAndDecodeSwapInstruction(signature, connection);
            }
        },
        "finalized"
    );
}

function isRaydiumSwap(instruction) {
    return (
        instruction.programId.toBase58() === RAYDIUM_PUBLIC_KEY &&
        instruction.accounts.length == 17
    );
}

async function fetchAndDecodeSwapInstruction(txId, connection) {
    const transaction = await connection.getParsedTransaction(txId, {
        commitment: "finalized",
        maxSupportedTransactionVersion: 0,
    });

    if (!transaction) {
        console.log("Transaction not found");
        return;
    }

    const instructions = transaction.transaction.message.instructions;
    const logMessages = transaction.meta.logMessages;
    const innerInstructions = transaction.meta.innerInstructions;

    let amount0 = "";
    let amount1 = "";

    let ammId = "";

    for (const innerInstruction of innerInstructions) {
        let i = 0;
        for (const instruction of innerInstruction.instructions) {
            if (isRaydiumSwap(instruction)) {
                amount0 = innerInstruction.instructions[i + 1].parsed.info.amount;
                amount1 = innerInstruction.instructions[i + 2].parsed.info.amount;
                ammId = instruction.accounts[1].toBase58();
            }
            i++;
        }
    }

    console.log(
        " WSOL: ",
        amount0,
        " TOKEN: ",
        amount1,
        "ammId: ",
        ammId,
        " signature: ",
        txId
    );
}

main(connection, raydium).catch(console.error);

