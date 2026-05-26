"""
数据备份与恢复 API
第三次迭代陈思言负责
"""
import os
import shutil
import sqlite3
from datetime import datetime
from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User
from app.decorators.auth import require_permission

backup_bp = Blueprint('backup', __name__)

# 备份存储目录
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)


def get_db_path():
    """获取数据库文件路径"""
    from app import db
    return db.engine.url.database


def get_backup_list():
    """获取备份列表"""
    backups = []
    if os.path.exists(BACKUP_DIR):
        for filename in sorted(os.listdir(BACKUP_DIR), reverse=True):
            if filename.endswith('.db'):
                filepath = os.path.join(BACKUP_DIR, filename)
                stat = os.stat(filepath)
                
                # 从文件名解析时间戳: backup_YYYYMMDD_HHMMSS.db
                created_at = datetime.fromtimestamp(stat.st_mtime)
                try:
                    # 提取文件名中的时间: backup_20260526_235637.db
                    parts = filename.replace('backup_', '').replace('.db', '').split('_')
                    if len(parts) == 2:
                        date_str = parts[0]  # 20260526
                        time_str = parts[1]  # 235637
                        created_at = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                except Exception:
                    pass  # 解析失败则用文件修改时间
                
                backups.append({
                    'filename': filename,
                    'created_at': created_at.isoformat(),
                    'size': round(stat.st_size / 1024 / 1024, 2),  # MB
                    'size_bytes': stat.st_size
                })
    return backups


@backup_bp.route('/list', methods=['GET'])
@jwt_required()
@require_permission('user_manage')
def list_backups():
    """获取备份列表"""
    backups = get_backup_list()
    return jsonify({
        'backups': backups,
        'total': len(backups)
    })


@backup_bp.route('/create', methods=['POST'])
@jwt_required()
@require_permission('user_manage')
def create_backup():
    """手动创建备份"""
    try:
        db_path = get_db_path()
        if not db_path or not os.path.exists(db_path):
            return jsonify({'message': '数据库文件不存在'}), 400
        
        # 生成备份文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'backup_{timestamp}.db'
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        # 复制数据库文件
        shutil.copy2(db_path, backup_path)
        
        # 获取备份信息
        stat = os.stat(backup_path)
        
        return jsonify({
            'message': '备份创建成功',
            'backup': {
                'filename': backup_filename,
                'created_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'size': round(stat.st_size / 1024 / 1024, 2)
            }
        })
    except Exception as e:
        return jsonify({'message': f'备份失败: {str(e)}'}), 500


@backup_bp.route('/download/<filename>', methods=['GET'])
@jwt_required()
@require_permission('user_manage')
def download_backup(filename):
    """下载备份文件"""
    try:
        # 安全检查：防止目录遍历
        if '..' in filename or '/' in filename:
            return jsonify({'message': '非法文件名'}), 400
        
        backup_path = os.path.join(BACKUP_DIR, filename)
        if not os.path.exists(backup_path):
            return jsonify({'message': '备份文件不存在'}), 404
        
        return send_file(backup_path, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'message': f'下载失败: {str(e)}'}), 500


@backup_bp.route('/restore/<filename>', methods=['POST'])
@jwt_required()
@require_permission('user_manage')
def restore_backup(filename):
    """从备份恢复数据"""
    try:
        # 安全检查
        if '..' in filename or '/' in filename:
            return jsonify({'message': '非法文件名'}), 400
        
        backup_path = os.path.join(BACKUP_DIR, filename)
        if not os.path.exists(backup_path):
            return jsonify({'message': '备份文件不存在'}), 404
        
        db_path = get_db_path()
        if not db_path:
            return jsonify({'message': '数据库路径错误'}), 500
        
        # 1. 先创建当前数据的紧急备份
        emergency_filename = f'emergency_before_restore_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        emergency_path = os.path.join(BACKUP_DIR, emergency_filename)
        shutil.copy2(db_path, emergency_path)
        
        # 2. 验证备份文件是否有效
        try:
            conn = sqlite3.connect(backup_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            conn.close()
            if len(tables) < 5:  # 基本表数量检查
                return jsonify({'message': '备份文件无效或已损坏'}), 400
        except Exception:
            return jsonify({'message': '备份文件无法读取'}), 400
        
        # 3. 恢复数据（替换数据库文件）
        shutil.copy2(backup_path, db_path)
        
        return jsonify({
            'message': '数据恢复成功',
            'emergency_backup': emergency_filename
        })
    except Exception as e:
        return jsonify({'message': f'恢复失败: {str(e)}'}), 500


@backup_bp.route('/delete/<filename>', methods=['DELETE'])
@jwt_required()
@require_permission('user_manage')
def delete_backup(filename):
    """删除备份文件"""
    try:
        if '..' in filename or '/' in filename:
            return jsonify({'message': '非法文件名'}), 400
        
        backup_path = os.path.join(BACKUP_DIR, filename)
        if not os.path.exists(backup_path):
            return jsonify({'message': '备份文件不存在'}), 404
        
        os.remove(backup_path)
        return jsonify({'message': '备份已删除'})
    except Exception as e:
        return jsonify({'message': f'删除失败: {str(e)}'}), 500
