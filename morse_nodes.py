def morse_to_text(morse_code: str) -> str:
    decoded_message = []
    
    MORSE_CODE_DICT = {
        'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
        'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
        'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
        'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
        'Y': '-.--', 'Z': '--..',
        '1': '.----', '2': '..---', '3': '...--', '4': '....-', '5': '.....',
        '6': '-....', '7': '--...', '8': '---..', '9': '----.', '0': '-----',
        ',': '--..--', '.': '.-.-.-', '?': '..--..', '/': '-..-.', '-': '-....-',
        '(': '-.--.', ')': '-.--.-', '!': '-.-.--', '&': '.-...', ':': '---...',
        ';': '-.-.-.', '=': '-...-', '+': '.-.-.', '_': '..--.-', '"': '.-..-.',
        '$': '...-..-', '@': '.--.-.'
    }

    MORSE_TO_CHAR_DICT = {code: char for char, code in MORSE_CODE_DICT.items()}

    morse_code = morse_code.replace('/', '  ')
    words = morse_code.strip().split('  ')

    for morse_word in words:
        decoded_word = ''
        morse_letters = morse_word.split(' ')

        for morse_letter in morse_letters:
            if morse_letter in MORSE_TO_CHAR_DICT:
                decoded_word += MORSE_TO_CHAR_DICT[morse_letter]
            elif morse_letter:
                decoded_word += '<?>'
        
        decoded_message.append(decoded_word)

    return ' '.join(decoded_message)

def text_to_morse(text: str) -> str:
    encoded_message = []
    MORSE_CODE_DICT = {
        'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
        'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
        'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
        'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
        'Y': '-.--', 'Z': '--..',
        '1': '.----', '2': '..---', '3': '...--', '4': '....-', '5': '.....',
        '6': '-....', '7': '--...', '8': '---..', '9': '----.', '0': '-----',
        ',': '--..--', '.': '.-.-.-', '?': '..--..', '/': '-..-.', '-': '-....-',
        '(': '-.--.', ')': '-.--.-', '!': '-.-.--', '&': '.-...', ':': '---...',
        ';': '-.-.-.', '=': '-...-', '+': '.-.-.', '_': '..--.-', '"': '.-..-.',
        '$': '...-..-', '@': '.--.-.'
    }
    
    
    words = text.upper().split()
    
    for word in words:
        encoded_word = []
        for char in word:
            morse_char = MORSE_CODE_DICT.get(char)
            if morse_char:
                encoded_word.append(morse_char)
        
        if encoded_word:
             encoded_message.append(' '.join(encoded_word))
    
    return ' / '.join(encoded_message)


class MorseCode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"default": "", "multiline": True}),
                "mode": (["encode", "decode"], {"default": "encode"}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("string",)
    FUNCTION = "convert"
    CATEGORY = "string"
    
    def convert(self, text, mode):
        if mode == "encode":
            s = text_to_morse(text)
            return (s,)
        s = morse_to_text(text)
        return (s,)
    
NODE_CLASS_MAPPINGS = {
    "MorseCode": MorseCode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MorseCode": "Morse Code",
}