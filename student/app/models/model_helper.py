"""
Model Template and Helper Functions
新しいモデルを追加する際のテンプレートとヘルパー関数
"""

def create_model_template(model_name: str, table_name: str = None) -> str:
    """
    新しいモデルファイルのテンプレートを生成
    
    Args:
        model_name: モデルクラス名
        table_name: テーブル名（指定しない場合はmodel_nameの小文字）
    
    Returns:
        モデルファイルの内容
    """
    if table_name is None:
        table_name = model_name.lower()
    
    template = f'''from ..database import db

class {model_name}(db.Model):
    __tablename__ = "{table_name}"
    
    id = db.Column(db.Integer, primary_key=True)
    # TODO: 必要なカラムを追加してください
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    def __repr__(self):
        return f'<{model_name}(id={{self.id}})>'
    
    def to_dict(self):
        """モデルを辞書形式に変換"""
        return {{
            'id': self.id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            # TODO: 他のフィールドを追加
        }}
'''
    
    return template

def generate_model_file(model_name: str, file_path: str = None, table_name: str = None):
    """
    新しいモデルファイルを生成
    
    Args:
        model_name: モデルクラス名
        file_path: 保存先パス（指定しない場合は自動生成）
        table_name: テーブル名
    """
    if file_path is None:
        file_path = f"{model_name.lower()}.py"
    
    template = create_model_template(model_name, table_name)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(template)
    
    print(f"Model file created: {file_path}")
    print(f"Class name: {model_name}")
    print("Don't forget to:")
    print("1. Add necessary columns to the model")
    print("2. Update the to_dict() method")
    print("3. Add any relationships or constraints")
    print("4. The model will be automatically imported when the app starts")

if __name__ == "__main__":
    # 使用例
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python model_helper.py <ModelName> [table_name]")
        print("Example: python model_helper.py Payment payment")
        sys.exit(1)
    
    model_name = sys.argv[1]
    table_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    generate_model_file(model_name, table_name=table_name)
