import os
from shutil import copyfile
import json
import sys
from pysqlcipher3 import dbapi2 as sqlite
import hashlib
import re
import json
import time
from jinja2 import Environment, FileSystemLoader

def get_conversations(conn):
    return conn.execute("SELECT id, name FROM conversations").fetchall()

def get_messages(conn, conversation_id):
    return conn.execute(f"SELECT json FROM messages where conversationId=\"{id}\" order by sent_at asc").fetchall()

def get_encryption_key(config_file):
    try:
        print(f"Opening config from {config_file}")
        with open(config_file) as f:
            config = json.load(f)
            key = config["key"]
            print(f"Found key starting with: {key[0:4]}...")
            return key
    except FileNotFoundError:
        print("Config file not found!")
        sys.exit(1)
    except KeyError:
        print("Config file does not contain key!")
        sys.exit(1)  

def get_connection(database, key):
    try:
        print(f"Trying to open database {database} (using sqlcipher 4)")
        conn = sqlite.connect(database)
        conn.execute(f"PRAGMA key = \"x'{key}'\"")
        conn.execute("SELECT * FROM sqlite_master").fetchall()
        return conn
    except sqlite.OperationalError as e:
        print(f"OperationalError: {e}")
        sys.exit(1)
    except sqlite.DatabaseError as e:
        try:
            print(f"Trying to open database {database} (using sqlcipher 3)")
            conn = sqlite.connect(database)
            conn.execute(f"PRAGMA key = \"x'{key}'\"")
            conn.execute("PRAGMA cipher_compatibility = 3")
            conn.execute("SELECT * FROM sqlite_master").fetchall()
            return conn
        except:
            print(f"DatabaseError: {e}")
            sys.exit(1)

def create_output_directory():
    timestamp = time.strftime("%Y%m%d_%H%M%S") 
    output_directory = os.path.join(os.getcwd(), f"signal_export_{timestamp}")
    os.mkdir(output_directory)
    os.mkdir(os.path.join(output_directory, 'conversations'))

    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", 'style.css')
    dest = os.path.join(output_directory, 'style.css')
    copyfile(src, dest)

    return output_directory

def get_conversation_filename(id, name):

    def get_valid_filename(s):
        s = str(s).strip().replace(' ', '_')
        return re.sub(r'(?u)[^-\w.]', '', s)

    hash = hashlib.md5(name.encode('utf-8')).hexdigest()
    return f"{get_valid_filename(name)}_{hash}.html"

def create_html_index(conversations, export_dir, env):
    
    conversation_links = []
    for (id, name) in conversations:
        conversation_links.append((name, get_conversation_filename(id, name)))
    
    template = env.get_template('index.html')
    output = template.render(timestamp=time.strftime("%Y-%m-%d %H:%M:%S"), conversation_links=conversation_links)

    with open(os.path.join(export_dir, 'index.html'), 'w') as output_file:
        output_file.write(output)
        output_file.close()

def parse_message_row(row_json):
    row = json.loads(row_json)

    if row.get("type") in ['incoming', 'outgoing']:
        mess_type = row.get("type")
    else:
        return None

    attachments = ''
    if "attachments" in row:
        for att in row.get("attachments"):
            attachments += "<br/>"
            if att.get("fileName") is not None:
                attachments += att.get("fileName")
            else:
                attachments += "[Filename unknown]"

    received = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(row["received_at"]/1000))
    body = row.get("body")

    return (mess_type, received, body, attachments)

def create_conversation_pages(conversations, output_directory, env):
    for (conversation_id, name) in conversations:
        print(f"Backing up '{name}'...")
        
        try:
            messages = get_messages(conn, conversation_id)
            message_data = []

            for (json) in messages:
                message_data.append(parse_message_row(json[0]))
            
            template = env.get_template('conversation.html')
            output = template.render(name=name, messages=message_data)

            with open(os.path.join(output_directory, "conversations", get_conversation_filename(conversation_id, name)), 'w') as output_file:
                output_file.write(output)
                output_file.close()

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    print(f'Starting Signal Desktop export...')

    if sys.platform == "darwin":
        signal_data_path = os.path.join(os.path.expanduser("~"), 'Library', 'Application Support', 'Signal')
        config_file_path = os.path.join(signal_data_path, "config.json")
        database_file_path = os.path.join(signal_data_path, "sql", "db.sqlite")
    else:
        print("Only MacOS tested so far, extiting.")
        sys.exit(0)

    conn = get_connection(database_file_path, get_encryption_key(config_file_path))
    output_directory = create_output_directory()

    conversations = get_conversations(conn)
    file_loader = FileSystemLoader(os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"))
    env = Environment(loader=file_loader)

    create_html_index(conversations, output_directory, env)
    create_conversation_pages(conversations, output_directory, env)

    

