polynomials = {
    "CRC-8": "100000111",                 # 9-bit generator polynomial
    "CRC-10": "11000000011",              # 11-bit generator polynomial
    "CRC-16": "11000000000000101",        # 17-bit generator polynomial
    "CRC-32": "100000100110000010001110110110111",  # 33-bit generator polynomial
}

polynomial = ""

def xor_division(dividend: str, divisor: str) -> str:
    """
    Performs bitwise XOR division (modulo-2 division) of a binary dividend by a binary divisor.
    Returns the remainder (CRC).
    """
    n = len(divisor)        
    pick = n                
    temp = dividend[:pick]  

    while pick < len(dividend):
        # If the leftmost bit is 1 perform XOR with divisor
        if temp[0] == '1':
            temp = format(int(temp, 2) ^ int(divisor, 2), '0' + str(n) + 'b')
            
        # Drop first bit and append next bit from dividend
        temp = temp[1:] + dividend[pick]
        pick += 1

    # One last XOR if leftmost bit is 1
    if temp[0] == '1':
        temp = format(int(temp, 2) ^ int(divisor, 2), '0' + str(n) + 'b')

    
    return temp[1:] # remainders leftmost bit is excluded as size will be sizeOf(divisor)-1

def gen_crc(dataword: str, polynomial: str)-> str:
    if not dataword:
        return ""
    
    if polynomial in polynomials:
        polynomial = polynomials[polynomial]
    
    dividend=dataword + '0' * (len(polynomial)-1)
    
    rem=xor_division(dividend, polynomial)
    
    new_data = dataword+rem
    
    return new_data

def verify_crc(codeword: str, polynomial: str)-> bool:
    if not codeword:
        return True
    
    if polynomial in polynomials:
        polynomial = polynomials[polynomial]
        
    rem=xor_division(codeword, polynomial)
    
    return int(rem,2) == 0

def main():
    # Example message
    data = "1101011011"

    # Choose polynomial
    poly_name = "CRC-10"

    print(f"Data:       {data}")
    print(f"Polynomial: {poly_name} -> {polynomials[poly_name]}")

    # Generate CRC
    codeword = gen_crc(data, poly_name)
    print(f"Codeword (Data + CRC): {codeword}")

    # Verify correct codeword
    is_valid = verify_crc(codeword, poly_name)
    print(f"Verification of correct codeword: {is_valid}")

    # Introduce error (flip last bit)
    corrupted = codeword[:-1] + ('1' if codeword[-1] == '0' else '0')
    print(f"Corrupted Codeword: {corrupted}")

    # Verify corrupted codeword
    is_valid_corrupted = verify_crc(corrupted, poly_name)
    print(f"Verification of corrupted codeword: {is_valid_corrupted}")


if __name__ == "__main__":
    main()
