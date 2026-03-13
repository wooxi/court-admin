#!/usr/bin/env python3
"""
修复数据库中的中文编码问题（双倍 UTF-8 编码）v2

核心原理：
- 正确的 "司礼监" UTF-8 编码应该是: E5 8F 85 E7 A4 BC E7 9B 91
- 但数据库中存储的是两层 UTF-8 编码
- 所以我们需要将存储的字节解码回原始的 UTF-8 字符串
"""
import pymysql
import sys

def fix_double_encoded_hex(hex_string):
    """
    修复双倍编码的 HEX 字符串
    
    参数：
    - hex_string: 例如 "C3A5C28FC2B8..."
    
    方法：
    - 将 HEX 字符串解析为字节
    - 每两个字节代表一个 Unicode 字符（在 Latin-1 范围内）
    - 这些字节实际上是 UTF-8 编码的 UTF-8 字符
    - 重新解码为正确的 UTF-8
    """
    try:
        #将 HEX 转换为字节
        raw_bytes = bytes.fromhex(hex_string)
        
        # 将字节按 Latin-1 解码为字符串（1:1 字节到字符映射）
        # 这会得到一个包含 Unicode 字符的字符串
        unicode_str = raw_bytes.decode('latin-1')
        
        # 将这些 Unicode 字符重新编码为字节
        # 然后用 UTF-8 解码
        fixed_str = unicode_str.encode('latin-1').decode('utf-8')
        
        return fixed_str
    except Exception as e:
        print(f"Warning: Cannot fix HEX {hex_string}, error: {e}")
        return None

def fix_with_known_mapping():
    """
    使用已知的正确值映射来修复数据
    """
    correct_values = {
        1: ('司礼监', '司礼监'),
        2: ('兵部', '兵部'),
        3: ('户部', '户部'),
        4: ('礼部', '礼部'),
        5: ('工部', '工部'),
        6: ('吏部', '吏部'),
        7: ('刑部', '刑部'),
    }
    return correct_values

def main():
    print("方式 1: 使用已知正确值修复")
    
    conn = pymysql.connect(
        host='192.168.100.4',
        port=3306,
        user='root',
        password='ulikem00n',
        database='court_admin',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    cursor = conn.cursor()
    
    try:
        # 直接使用已知的正确值更新数据库
        correct_values = fix_with_known_mapping()
        
        for minister_id, (name, dept) in correct_values.items():
            print(f"更新 ID {minister_id}: name='{name}', dept='{dept}'")
            cursor.execute(
                'UPDATE ministers SET name = %s, department = %s WHERE id = %s',
                (name, dept, minister_id)
            )
        
        conn.commit()
        
        # 验证
        print("\n验证修复结果：")
        cursor.execute('SELECT id, name, department FROM ministers ORDER BY id')
        rows = cursor.fetchall()
        
        for row in rows:
            print(f"  ID {row['id']}: name='{row['name']}', dept='{row['department']}'")
        
        # 检查 HEX
        print("\n检查 HEX 值：")
        cursor.execute('SELECT id, HEX(name) as hex_name FROM ministers ORDER BY id')
        rows = cursor.fetchall()
        
        for row in rows:
            print(f"  ID {row['id']}: {row['hex_name']}")
        
        print("\n✅ 修复完成！")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()
