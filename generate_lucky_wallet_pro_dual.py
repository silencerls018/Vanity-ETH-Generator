from eth_account import Account
import time
import multiprocessing

# 启用未审核的HD钱包功能
Account.enable_unaudited_hdwallet_features()

# 目标模式：按长度降序排列
PATTERNS = ['88888888', '8888888', '888888']
OUTPUT_FILE = "wallets_with_888_pro_dual.txt"

def generate_and_check_wallet(_):
    """
    生成一个钱包，检查其地址是否符合开头和/或结尾的模式。
    如果符合，返回钱包信息；否则返回None。
    这个版本可以检测并记录多个匹配项。
    """
    account, mnemonic = Account.create_with_mnemonic()
    address = account.address
    address_no_prefix = address[2:].lower()
    
    found_matches = [] # 使用一个列表来存储所有找到的匹配项
    
    # --- 检查前缀 ---
    # 检查所有前缀模式，只记录最长的那一个
    for pattern in PATTERNS:
        if address_no_prefix.startswith(pattern):
            found_matches.append({"pattern": pattern, "type": "Prefix"})
            break # 找到最长的前缀后就停止，避免记录'888888'又记录'8888888'

    # --- 检查后缀 ---
    # 检查所有后缀模式，只记录最长的那一个
    for pattern in PATTERNS:
        if address_no_prefix.endswith(pattern):
            found_matches.append({"pattern": pattern, "type": "Suffix"})
            break # 找到最长的后缀后就停止

    # 如果列表不为空，说明至少有一个匹配项
    if found_matches:
        private_key = account.key.hex()
        return (address, private_key, mnemonic, found_matches)
            
    return None

def save_wallet(address, private_key, mnemonic, matches):
    """将找到的钱包信息保存到文件，可以处理多个匹配项"""
    # 将匹配详情格式化成更易读的字符串
    match_details = " & ".join([f"{m['pattern']} ({m['type']})" for m in matches])
    
    with open(OUTPUT_FILE, 'a') as f:
        f.write(f"Address: {address}\n")
        f.write(f"Private Key: {private_key}\n")
        f.write(f"Mnemonic: {mnemonic}\n")
        f.write(f"Match Details: {match_details}\n") # 使用新的字段记录详情
        f.write(f"{'-'*50}\n")
        
    print(f"\n!!! Found matching wallet! Address: {address} | Details: {match_details} !!!\n")

def main():
    # (main函数和之前完全一样，无需改动)
    try:
        cpu_cores = multiprocessing.cpu_count()
    except NotImplementedError:
        cpu_cores = 4
        
    print(f"Starting wallet generation on {cpu_cores} CPU cores...")
    print(f"Looking for addresses starting or ending with: {', '.join(PATTERNS)}")
    
    pool = multiprocessing.Pool(processes=cpu_cores)
    total_count = 0
    start_time = time.time()
    chunk_size = cpu_cores * 2000 

    while True:
        try:
            results = pool.imap_unordered(generate_and_check_wallet, range(chunk_size), chunksize=500)
            
            for result in results:
                total_count += 1
                if result:
                    address, private_key, mnemonic, matches = result
                    save_wallet(address, private_key, mnemonic, matches)
            
            elapsed_time = time.time() - start_time
            if elapsed_time > 0:
                rate = total_count / elapsed_time
                print(f"\rGenerated {total_count} wallets | Speed: {rate:,.2f} wallets/sec", end="")

        except KeyboardInterrupt:
            print("\nStopping process...")
            pool.terminate()
            pool.join()
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            break

if __name__ == "__main__":
    main()