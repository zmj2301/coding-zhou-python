import re
import string


class AIEnhancer:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        
        self.pause_words = {
            '，', ',', '。', '.', '！', '!', '？', '?', '；', ';', '：', ':',
            '、', '…', '—', '　', ' ', '\t', '\n'
        }
        
        self.number_mapping = {
            '0': '零', '1': '一', '2': '二', '3': '三', '4': '四',
            '5': '五', '6': '六', '7': '七', '8': '八', '9': '九'
        }
        
        self.unit_mapping = {
            '10': '十', '100': '百', '1000': '千', '10000': '万', '100000000': '亿'
        }
        
        self.common_abbreviations = {
            'vs': '对', 'etc': '等等', 'e.g.': '例如', 'i.e.': '也就是',
            'Mr.': '先生', 'Mrs.': '女士', 'Dr.': '博士', 'Prof.': '教授',
            'St.': '街道', 'Rd.': '路', 'Ave.': '大道'
        }
    
    def test_api_connection(self, api_key=None, api_provider=None):
        return True, "已切换为本地文本优化模式，无需API密钥"
    
    def optimize_text(self, text):
        try:
            optimized = text
            
            optimized = self._normalize_spaces(optimized)
            optimized = self._handle_punctuation(optimized)
            optimized = self._convert_numbers(optimized)
            optimized = self._handle_abbreviations(optimized)
            optimized = self._add_proper_pauses(optimized)
            optimized = self._handle_special_chars(optimized)
            optimized = self._improve_readability(optimized)
            optimized = self._cleanup_text(optimized)
            
            return True, "文本优化完成", optimized
        except Exception as e:
            print(f"优化失败: {e}")
            return False, f"优化失败: {str(e)}", text
    
    def _normalize_spaces(self, text):
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'([，。！？；：])\s*', r'\1', text)
        return text.strip()
    
    def _handle_punctuation(self, text):
        text = text.replace('“', '"').replace('”', '"')
        text = text.replace('‘', "'").replace('’', "'")
        text = text.replace('【', '[').replace('】', ']')
        text = text.replace('（', '(').replace('）', ')')
        text = text.replace('《', '<').replace('》', '>')
        return text
    
    def _convert_numbers(self, text):
        def replace_year(match):
            year = match.group(1)
            result = ''
            for d in year:
                if d in self.number_mapping:
                    result += self.number_mapping[d]
                else:
                    result += d
            return result + '年'
        
        def replace_number(match):
            num_str = match.group(1)
            return self._chinese_number(num_str)
        
        text = re.sub(r'(\d{4})年', replace_year, text)
        text = re.sub(r'(\d+(?:\.\d+)?)', replace_number, text)
        return text
    
    def _chinese_number(self, num_str):
        try:
            if '.' in num_str:
                integer_part, decimal_part = num_str.split('.', 1)
                result = self._integer_to_chinese(integer_part) + '点'
                for d in decimal_part:
                    if d in self.number_mapping:
                        result += self.number_mapping[d]
                return result
            else:
                return self._integer_to_chinese(num_str)
        except:
            return num_str
    
    def _integer_to_chinese(self, num_str):
        try:
            num = int(num_str)
            
            if num == 0:
                return '零'
            
            digits = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九']
            units = ['', '十', '百', '千']
            big_units = ['', '万', '亿']
            
            num_str = str(num)
            length = len(num_str)
            
            result = []
            
            groups = []
            while num_str:
                groups.append(num_str[-4:])
                num_str = num_str[:-4]
            groups = groups[::-1]
            
            for i, group in enumerate(groups):
                group_result = []
                group_length = len(group)
                
                for j, digit in enumerate(group):
                    d = int(digit)
                    unit_pos = group_length - j - 1
                    
                    if d == 0:
                        if group_result and group_result[-1] != '零':
                            group_result.append('零')
                    else:
                        group_result.append(digits[d])
                        group_result.append(units[unit_pos])
                
                if group_result and group_result[-1] == '零':
                    group_result = group_result[:-1]
                
                if group_result:
                    result.extend(group_result)
                    if i < len(groups) - 1:
                        result.append(big_units[len(groups) - 1 - i])
            
            if result and result[0] == '一' and result[1] == '十':
                result = result[1:]
            
            final = ''.join(result)
            return final if final else num_str
        except:
            return num_str
    
    def _handle_abbreviations(self, text):
        for abbr, full in self.common_abbreviations.items():
            text = re.sub(re.escape(abbr), full, text, flags=re.IGNORECASE)
        return text
    
    def _add_proper_pauses(self, text):
        text = re.sub(r'([；：，。！？])(?!\s|$)', r'\1 ', text)
        text = re.sub(r'(\w{15,})', lambda m: self._split_long_word(m.group(1)), text)
        return text
    
    def _split_long_word(self, word):
        if len(word) <= 10:
            return word
        
        parts = []
        for i in range(0, len(word), 10):
            parts.append(word[i:i+10])
        
        return '，'.join(parts)
    
    def _handle_special_chars(self, text):
        special_chars = ['*', '#', '@', '^', '&', '%', '$', '~', '`']
        for char in special_chars:
            text = text.replace(char, ' ')
        
        text = text.replace('\n', '。').replace('\r', '')
        text = text.replace('\t', ' ')
        
        return text
    
    def _improve_readability(self, text):
        text = re.sub(r'([。！？])([^\s])', r'\1 \2', text)
        text = re.sub(r',', '，', text)
        text = re.sub(r'\.', '。', text)
        text = re.sub(r'!', '！', text)
        text = re.sub(r'\?', '？', text)
        text = re.sub(r':', '：', text)
        text = re.sub(r';', '；', text)
        
        return text
    
    def _cleanup_text(self, text):
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'，，+', '，', text)
        text = re.sub(r'。。+', '。', text)
        text = re.sub(r'[，。]\s*[，。]', '。', text)
        
        return text.strip()
