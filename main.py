import asyncio
import json

from web3.contract import AsyncContract

from ClientBase import ClientBase

address_contract_usdc_base = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
sender_text = "отправителя"
recipient_text = "получателя"

def get_private_key_by_input():
    while True:
        private_key_by_input = input(f"Введите приватный ключ отправителя: ")
        if len(private_key_by_input) == 64:
            return private_key_by_input
        else:
            print("Введен некорректный приватный ключ, повторите попытку!")


def get_address_by_input(client, whose):
    while True:
        try:
            address_input = input(f"Введите адрес {whose}: ")
            return client.w3.to_checksum_address(address_input)
        except ValueError:
            print("Некорректно указан адрес кошелька, повторите попытку")

def get_value_for_tx_by_input(client):
    while True:
        try:
            value = float(input("Введите количество для отправки (USDC): "))
            if value> 0.1:
                return client.w3.to_wei(value, 'mwei')
            else:
                print("Введено значение меньше 0.1 USDC,  укажите больше значение")
        except ValueError:
            print("Некорректно указано количество для отправки (USDC), повторите попытку")

def read_file_abi():
    with open("base_fiat_proxy_abi.json", "r", encoding="utf-8") as file:
        return json.load(file)

async def print_check_balance(contract, address, whose, is_after = False):
    balance = await contract.functions.balanceOf(address).call()
    decimals = await contract.functions.decimals().call()

    if is_after:
        print(f"Баланс {whose} после: {balance / 10 ** decimals} USDC")
    else:
        print (f"Баланс {whose} до: {balance / 10 ** decimals} USDC")
    return balance

async def build_transaction(client, contract, to_address, amount):
    # Получаем базовую цену газа и приоритетную комиссию
    base_fee = await client.w3.eth.gas_price
    max_priority_fee_per_gas = await client.w3.eth.max_priority_fee
    max_fee_per_gas = base_fee + max_priority_fee_per_gas

    return await contract.functions.transfer(to_address, amount).build_transaction({
        'nonce':await client.w3.eth.get_transaction_count(client.address),
        'from': client.address,
        # 'to': client.w3.to_checksum_address(to_address),
        # 'value': amount,
        # 'gas': 21000,
        'maxPriorityFeePerGas': max_priority_fee_per_gas,
        'maxFeePerGas': max_fee_per_gas,
        'chainId': await client.w3.eth.chain_id
    })

async def main():
    private_key =  get_private_key_by_input()
    client = ClientBase(private_key)

    address_sender = get_address_by_input(client, sender_text)
    address_recipient = get_address_by_input(client, recipient_text)

    usdc_contract: AsyncContract = client.w3.eth.contract(
        address=client.w3.to_checksum_address(address_contract_usdc_base),
        abi=read_file_abi()
    )

    print("\n")
    await print_check_balance(usdc_contract, address_sender, sender_text)
    await print_check_balance(usdc_contract, address_recipient, recipient_text)
    print("\n")

    value_for_tx = get_value_for_tx_by_input(client)

    if await client.control_balance():
        print("\n🚀 Создание и отправка транзакции...")
        transaction = await build_transaction(client, usdc_contract, address_recipient, value_for_tx)
        tx_hash_hex = await client.sign_and_send_tx(transaction)

        if tx_hash_hex:
            await client.wait_tx(tx_hash_hex)

            await print_check_balance(usdc_contract, address_sender, sender_text, True)
            await print_check_balance(usdc_contract, address_recipient, recipient_text, True)
        else:
            print("❌ Транзакция не выполнена из-за недостатка средств.")

if __name__ == "__main__":
    asyncio.run(main())
