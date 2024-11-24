import asyncio

from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.exceptions import TransactionNotFound

class ClientBase:
    def __init__(self, private_key):
        self.private_key = private_key
        rpc_url = 'https://base-pokt.nodies.app'
        self.explorer_url = 'https://basescan.org/'
        self.w3 = AsyncWeb3(AsyncHTTPProvider(rpc_url))
        self.address = self.w3.to_checksum_address(self.w3.eth.account.from_key(self.private_key).address)

    async def sign_and_send_tx(self, transaction):
        try:
            signed_raw_tx = self.w3.eth.account.sign_transaction(transaction, self.private_key).rawTransaction
            # print('Successfully signed transaction!')
            tx_hash_bytes = await self.w3.eth.send_raw_transaction(signed_raw_tx)
            # print('Successfully sent transaction!')
            tx_hash_hex = self.w3.to_hex(tx_hash_bytes)
            return tx_hash_hex
        except Exception as error:
            print(f"❌ Ошибка при отправке транзакции: {error}")
            return None

    # Проверка достаточности баланса с учетом стоимсоти газа
    async def control_balance(self):
        balance = await self.w3.eth.get_balance(self.address)
        gas_price = await self.w3.eth.gas_price
        gas_limit = 21000
        total_cost = gas_price * gas_limit * 1.5

        if balance >= total_cost:
            return True
        else:
            print("⚠️ Недостаточно средств для транзакции. Проверьте баланс.")
            return False

    async def wait_tx(self, tx_hash):
        total_time = 0
        timeout = 120
        poll_latency = 10
        while True:
            try:
                receipt = await self.w3.eth.wait_for_transaction_receipt(tx_hash)
                if receipt.status == 1:
                    print(f'\nТранзакция отправлена! Хэш транзакции: {tx_hash}')
                    print(f'Ссылка: {self.explorer_url}tx/{tx_hash}\n')
                    return
                elif receipt.status is None:
                    await asyncio.sleep(poll_latency)
                else:
                    print(f'\nTransaction failed: {self.explorer_url}tx/{tx_hash}\n')
            except TransactionNotFound:
                if total_time > timeout:
                    print(f"\nTransaction is not in the chain after {timeout} seconds\n")
                total_time += poll_latency
                await asyncio.sleep(poll_latency)
