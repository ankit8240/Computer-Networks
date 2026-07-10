chunk = 16
bit_size = 4

def gen_checksum(data: str)->str:
    n = len(data)
    if n % chunk != 0:
        data = '0'*(chunk - n % chunk) + data #padding
        n = len(data)
    
    words = [data[i:i+chunk] for i in range(0, n, chunk)]
    checksum_strs = []
    
    for word in words: 
        numbers = [int(word[i:i+bit_size], 2) for i in range(0, chunk, bit_size)] #4 numbers from chunk size=16 each of bit size=4
        checksum=sum(numbers)
        
        while checksum >= (1 << bit_size):
            carry = checksum >> bit_size          # overflow part
            lower_bits = checksum & ((1 << bit_size) - 1)  # keep only bit_size bits
            checksum = carry + lower_bits
        
        checksum_str = format(checksum, '0{}b'.format(bit_size))
        # complementing that now
        checksum_str_comp = ''.join('0' if b == '1' else '1' for b in checksum_str)
        checksum_strs.append(word + checksum_str_comp)
        
    return ''.join(checksum_strs)

def verify_checksum(data: str)->bool:
    n = len(data)
    word_len = chunk + bit_size
    if n % word_len != 0:
        data = '0'*(word_len - n % word_len) + data #padding
        n = len(data)
    
    words = [data[i:i+word_len] for i in range(0, n, word_len)]
    
    for word in words:
        numbers = [int(word[i:i+bit_size], 2) for i in range(0, len(word), bit_size)] 
        
        checksum=sum(numbers)
        
        limit = 1 << bit_size   # e.g., 16 if bit_size=4
        while checksum >= limit:
            carry = checksum // limit      # overflow part
            checksum = (checksum % limit) + carry  # lower bits + carry
            
        all_ones = limit - 1   # e.g., 15 if bit_size=4
        if checksum != all_ones:
            return False

    return True


def main():

    data = "1101011011"
    
    print(f"Data:       {data}")
    
    codeword = gen_checksum(data)
    print(f"Codeword (Data + CheckSum): {codeword}")

    # Verify correct codeword
    is_valid = verify_checksum(codeword)
    print(f"Verification of correct codeword: {is_valid}")

    # Introduce error (flip last bit)
    corrupted = codeword[:-1] + ('1' if codeword[-1] == '0' else '0')
    print(f"Corrupted Codeword: {corrupted}")

    # Verify corrupted codeword
    is_valid_corrupted = verify_checksum(corrupted)
    print(f"Verification of corrupted codeword: {is_valid_corrupted}")


if __name__ == "__main__":
    main()
