from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
from .models.database import DatabaseManager
import threading
import webbrowser
import time
import os
import hashlib

app = Flask(__name__)
db_manager = None
secret_key = "SecretKey"  # 默认密钥

def init_webui(db_mgr, sec_key):
    """初始化WebUI"""
    global db_manager, secret_key
    db_manager = db_mgr
    secret_key = sec_key
    app.secret_key = hashlib.sha256(sec_key.encode()).hexdigest()

# 登录页面路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        key = request.form['key']
        if key == secret_key:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash('密钥错误，请重新输入')
    return render_template('login.html')

# 登出路由
@app.route('/logout')
def logout():
    """登出"""
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# 验证登录装饰器
def login_required(f):
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# 首页路由
@app.route('/')
@login_required
def index():
    """首页"""
    return render_template('index.html')

# 用户管理路由
@app.route('/users')
@login_required
def user_management():
    """用户管理页面"""
    return render_template('user_management.html')

@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
    """获取所有用户数据"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    users = db_manager.fetch_all("SELECT * FROM users ORDER BY level DESC, exp DESC")
    user_list = []
    for user in users:
        user_list.append({
            'user_id': user['user_id'],
            'platform': user['platform'],
            'nickname': user['nickname'],
            'gold': user['gold'],
            'exp': user['exp'],
            'level': user['level'],
            'fishing_count': user['fishing_count'],
            'total_fish_weight': user['total_fish_weight'],
            'total_income': user['total_income'],
            'auto_fishing': user['auto_fishing'],
            'last_fishing_time': user['last_fishing_time'],
            'created_at': user['created_at'],
            'updated_at': user['updated_at']
        })
    return jsonify(user_list)

@app.route('/api/users', methods=['POST'])
@login_required
def add_user():
    """添加用户"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    try:
        data = request.get_json()
        user_id = data.get('user_id')
        nickname = data.get('nickname')
        gold = data.get('gold', 100)
        exp = data.get('exp', 0)
        level = data.get('level', 1)

        if not all([user_id, nickname]):
            return jsonify({'error': 'Missing required fields'}), 400

        # 检查用户是否已存在
        existing_user = db_manager.fetch_one("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if existing_user:
            return jsonify({'error': 'User already exists'}), 400

        current_time = int(time.time())
        db_manager.execute_query(
            """INSERT INTO users
               (user_id, platform, nickname, gold, exp, level, fishing_count, total_fish_weight, total_income,
                auto_fishing, last_fishing_time, created_at, updated_at)
               VALUES (?, 'unknown', ?, ?, ?, ?, 0, 0, 0, FALSE, 0, ?, ?)""",
            (user_id, nickname, gold, exp, level, current_time, current_time)
        )

        return jsonify({'message': 'User added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    """更新用户"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    try:
        data = request.get_json()
        nickname = data.get('nickname')
        gold = data.get('gold')
        exp = data.get('exp')
        level = data.get('level')
        auto_fishing = data.get('auto_fishing', False)

        if not all([nickname, gold, exp, level]):
            return jsonify({'error': 'Missing required fields'}), 400

        updated_at = int(time.time())
        db_manager.execute_query(
            """UPDATE users SET
               nickname=?, gold=?, exp=?, level=?, auto_fishing=?, updated_at=?
               WHERE user_id=?""",
            (nickname, gold, exp, level, auto_fishing, updated_at, user_id)
        )

        return jsonify({'message': 'User updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    """删除用户"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    try:
        # 删除用户的关联数据
        db_manager.execute_query("DELETE FROM user_fish_inventory WHERE user_id=?", (user_id,))
        db_manager.execute_query("DELETE FROM user_rod_instances WHERE user_id=?", (user_id,))
        db_manager.execute_query("DELETE FROM user_accessory_instances WHERE user_id=?", (user_id,))
        db_manager.execute_query("DELETE FROM user_bait_inventory WHERE user_id=?", (user_id,))
        db_manager.execute_query("DELETE FROM fishing_logs WHERE user_id=?", (user_id,))
        db_manager.execute_query("DELETE FROM gacha_logs WHERE user_id=?", (user_id,))
        db_manager.execute_query("DELETE FROM market_listings WHERE seller_user_id=?", (user_id,))
        db_manager.execute_query("DELETE FROM user_achievements WHERE user_id=?", (user_id,))
        db_manager.execute_query("DELETE FROM user_titles WHERE user_id=?", (user_id,))
        db_manager.execute_query("DELETE FROM tax_logs WHERE user_id=?", (user_id,))
        db_manager.execute_query("DELETE FROM sign_in_logs WHERE user_id=?", (user_id,))

        # 删除用户
        db_manager.execute_query("DELETE FROM users WHERE user_id=?", (user_id,))

        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 鱼类数据路由
@app.route('/fish')
@login_required
def fish_data():
    """鱼类数据页面"""
    return render_template('fish_data.html')

@app.route('/api/fish', methods=['GET'])
@login_required
def get_fish_data():
    """获取所有鱼类数据"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    fish_templates = db_manager.fetch_all("SELECT * FROM fish_templates ORDER BY rarity, id")
    fish_list = []
    for fish in fish_templates:
        fish_list.append({
            'id': fish['id'],
            'name': fish['name'],
            'description': fish['description'],
            'rarity': fish['rarity'],
            'base_value': fish['base_value'],
            'min_weight': fish['min_weight'],
            'max_weight': fish['max_weight'],
            'icon_url': fish['icon_url']
        })
    return jsonify(fish_list)

@app.route('/api/fish', methods=['POST'])
@login_required
def add_fish():
    """添加鱼类"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        rarity = data.get('rarity')
        base_value = data.get('base_value')
        min_weight = data.get('min_weight')
        max_weight = data.get('max_weight')

        if not all([name, rarity, base_value, min_weight, max_weight]):
            return jsonify({'error': 'Missing required fields'}), 400

        db_manager.execute_query(
            """INSERT INTO fish_templates
               (name, description, rarity, base_value, min_weight, max_weight)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, description, rarity, base_value, min_weight, max_weight)
        )

        return jsonify({'message': 'Fish added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fish/<int:fish_id>', methods=['PUT'])
@login_required
def update_fish(fish_id):
    """更新鱼类"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        rarity = data.get('rarity')
        base_value = data.get('base_value')
        min_weight = data.get('min_weight')
        max_weight = data.get('max_weight')

        if not all([name, rarity, base_value, min_weight, max_weight]):
            return jsonify({'error': 'Missing required fields'}), 400

        db_manager.execute_query(
            """UPDATE fish_templates SET
               name=?, description=?, rarity=?, base_value=?, min_weight=?, max_weight=?
               WHERE id=?""",
            (name, description, rarity, base_value, min_weight, max_weight, fish_id)
        )

        return jsonify({'message': 'Fish updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fish/<int:fish_id>', methods=['DELETE'])
@login_required
def delete_fish(fish_id):
    """删除鱼类"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    try:
        db_manager.execute_query("DELETE FROM fish_templates WHERE id=?", (fish_id,))
        return jsonify({'message': 'Fish deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fish/<int:fish_id>')
@login_required
def get_fish_detail(fish_id):
    """获取特定鱼类详情"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    fish = db_manager.fetch_one("SELECT * FROM fish_templates WHERE id = ?", (fish_id,))
    if fish:
        return jsonify({
            'id': fish['id'],
            'name': fish['name'],
            'description': fish['description'],
            'rarity': fish['rarity'],
            'base_value': fish['base_value'],
            'min_weight': fish['min_weight'],
            'max_weight': fish['max_weight'],
            'icon_url': fish['icon_url']
        })
    return jsonify({'error': 'Fish not found'}), 404

# 鱼竿数据路由
@app.route('/rods')
@login_required
def rod_data():
    """鱼竿数据页面"""
    return render_template('rod_data.html')

@app.route('/api/rods')
@login_required
def get_rod_data():
    """获取所有鱼竿数据"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    rod_templates = db_manager.fetch_all("SELECT * FROM rod_templates ORDER BY rarity, id")
    rod_list = []
    for rod in rod_templates:
        rod_list.append({
            'id': rod['id'],
            'name': rod['name'],
            'description': rod['description'],
            'rarity': rod['rarity'],
            'source': rod['source'],
            'purchase_cost': rod['purchase_cost'],
            'quality_mod': rod['quality_mod'],
            'quantity_mod': rod['quantity_mod'],
            'rare_mod': rod['rare_mod'],
            'durability': rod['durability'],
            'icon_url': rod['icon_url']
        })
    return jsonify(rod_list)

# 饰品数据路由
@app.route('/accessories')
@login_required
def accessory_data():
    """饰品数据页面"""
    return render_template('accessory_data.html')

@app.route('/api/accessories')
@login_required
def get_accessory_data():
    """获取所有饰品数据"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    accessory_templates = db_manager.fetch_all("SELECT * FROM accessory_templates ORDER BY rarity, id")
    accessory_list = []
    for accessory in accessory_templates:
        accessory_list.append({
            'id': accessory['id'],
            'name': accessory['name'],
            'description': accessory['description'],
            'rarity': accessory['rarity'],
            'slot_type': accessory['slot_type'],
            'quality_mod': accessory['quality_mod'],
            'quantity_mod': accessory['quantity_mod'],
            'rare_mod': accessory['rare_mod'],
            'coin_mod': accessory['coin_mod'],
            'other_desc': accessory['other_desc'],
            'icon_url': accessory['icon_url']
        })
    return jsonify(accessory_list)

# 鱼饵数据路由
@app.route('/baits')
@login_required
def bait_data():
    """鱼饵数据页面"""
    return render_template('bait_data.html')

@app.route('/api/baits')
@login_required
def get_bait_data():
    """获取所有鱼饵数据"""
    if not db_manager:
        return jsonify({'error': 'Database not initialized'}), 500

    bait_templates = db_manager.fetch_all("SELECT * FROM bait_templates ORDER BY rarity, id")
    bait_list = []
    for bait in bait_templates:
        bait_list.append({
            'id': bait['id'],
            'name': bait['name'],
            'description': bait['description'],
            'rarity': bait['rarity'],
            'effect_description': bait['effect_description'],
            'duration_minutes': bait['duration_minutes'],
            'cost': bait['cost'],
            'required_rod_rarity': bait['required_rod_rarity'],
            'success_rate_modifier': bait['success_rate_modifier'],
            'rare_chance_modifier': bait['rare_chance_modifier'],
            'garbage_reduction_modifier': bait['garbage_reduction_modifier'],
            'value_modifier': bait['value_modifier'],
            'quantity_modifier': bait['quantity_modifier'],
            'is_consumable': bait['is_consumable']
        })
    return jsonify(bait_list)

def start_webui(port):
    """启动WebUI"""
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    # 在单独的线程中启动Web服务器
    server_thread = threading.Thread(target=start_webui, args=(6200,))
    server_thread.daemon = True
    server_thread.start()

    # 等待服务器启动
    time.sleep(2)

    # 打开浏览器
    webbrowser.open('http://localhost:6200')

    # 保持主线程运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("服务器已关闭")