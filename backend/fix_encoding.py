#!/usr/bin/env python3
"""
修复数据库中的中文编码问题（双倍 UTF-8 编码）
"""
import pymysql
import sys

def fix_double_encoded_utf8(text):
    """
    修复双倍编码的 UTF-8 字符串
    
    原理：
    - 正确的 UTF-8 字符 "司" 的编码是 E5 8F 85
    - 但数据库中存储的是 E5 8F 85 被再次编码为 UTF-8：C3 A5 C2 8F C2 B8
    - 所以我们需要将 C3 A5 C2 8F C2 B8 解码回 E5 8F 85
    
    方法：
    1. 字符串包含的是 Latin-1 范围内的字符（0-255）
    2. 将字符串编码为 Latin-1 字节
    3. 将这些字节解码为 UTF-8
    """
    try:
        # 获取字符串的 Latin-1 字节表示
        # 这些字节实际上是双倍编码的 UTF-8
        latin1_bytes = text.encode('latin1')
        # 将字节解码为正确的 UTF-8 字符串
        fixed = latin1_bytes.decode('utf-8')
        return fixed
    except (UnicodeEncodeError, UnicodeDecodeError) as e:
        print(f"Warning: Cannot fix text: {repr(text)}, error: {e}")
        return text

def main():
    # 连接数据库
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
        # 修复 ministers 表
        print("正在修复 ministers 表...")
        cursor.execute('SELECT id, name, department FROM ministers')
        rows = cursor.fetchall()
        
        for row in rows:
            fixed_name = fix_double_encoded_utf8(row['name'])
            fixed_dept = fix_double_encoded_utf8(row['department'])
            
            if fixed_name != row['name']:
                print(f"  ID {row['id']}: '{row['name']}' -> '{fixed_name}'")
                cursor.execute(
                    'UPDATE ministers SET name = %s WHERE id = %s',
                    (fixed_name, row['id'])
                )
            if fixed_dept != row['department']:
                print(f"  ID {row['id']}: dept '{row['department']}' -> '{fixed_dept}'")
                cursor.execute(
                    'UPDATE ministers SET department = %s WHERE id = %s',
                    (fixed_dept, row['id'])
                )
        
        conn.commit()
        
        # 验证修复结果
        print("\n验证修复结果：")
        cursor.execute('SELECT id, name, department FROM ministers')
        rows = cursor.fetchall()
        
        for row in rows:
            print(f"  ID {row['id']}: name='{row['name']}', dept='{row['department']}'")
        
        print("\n✅ 修复完成！")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()
