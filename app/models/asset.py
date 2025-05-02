from datetime import datetime
from app import db

class Asset(db.Model):
    """Asset model representing Barang Milik Negara (BMN)"""
    __tablename__ = 'assets'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.String(50), unique=True, index=True, nullable=False, comment="Nomor Unik Aset")
    asset_code = db.Column(db.String(20), index=True, nullable=False, comment="Kode Barang sesuai Kodefikasi BMN")
    asset_name = db.Column(db.String(255), nullable=False, comment="Nama Barang")
    asset_condition = db.Column(db.String(20), nullable=False, comment="Kondisi Barang (Baik/Rusak Ringan/Rusak Berat)")
    acquisition_date = db.Column(db.Date, nullable=True, comment="Tanggal Perolehan")
    acquisition_value = db.Column(db.Numeric(15, 2), nullable=True, comment="Nilai Perolehan")
    location = db.Column(db.String(255), nullable=True, comment="Lokasi Barang")
    usage_status = db.Column(db.String(50), nullable=True, comment="Status Penggunaan")
    satker_id = db.Column(db.Integer, db.ForeignKey('satkers.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, asset_id, asset_code, asset_name, asset_condition, satker_id, **kwargs):
        self.asset_id = asset_id
        self.asset_code = asset_code
        self.asset_name = asset_name
        self.asset_condition = asset_condition
        self.satker_id = satker_id
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def get_asset_details(self):
        """Return a dictionary with asset details"""
        return {
            'id': self.id,
            'asset_id': self.asset_id,
            'asset_code': self.asset_code,
            'asset_name': self.asset_name,
            'asset_condition': self.asset_condition,
            'acquisition_date': self.acquisition_date,
            'acquisition_value': self.acquisition_value,
            'location': self.location,
            'usage_status': self.usage_status,
            'satker_id': self.satker_id
        }
    
    def validate_condition(self):
        """Validate if the asset condition is valid"""
        valid_conditions = ['Baik', 'Rusak Ringan', 'Rusak Berat']
        return self.asset_condition in valid_conditions
    
    def check_compliance(self):
        """Check if the asset complies with the standards"""
        # This method will be implemented with specific business logic
        # based on asset type and PMK 138 Tahun 2024
        return True
    
    def get_asset_class(self):
        """Get asset classification based on asset code"""
        # Asset classification logic based on PMK 138 Tahun 2024
        # The first 2 digits represent the asset group
        asset_group = self.asset_code[:2]
        
        asset_groups = {
            '01': 'Tanah',
            '02': 'Peralatan dan Mesin',
            '03': 'Gedung dan Bangunan',
            '04': 'Jalan, Irigasi, dan Jaringan',
            '05': 'Aset Tetap Lainnya',
            '06': 'Konstruksi Dalam Pengerjaan',
            '07': 'Aset Tak Berwujud'
        }
        
        return asset_groups.get(asset_group, 'Tidak Diketahui')
    
    def __repr__(self):
        return f'<Asset {self.asset_id} {self.asset_name}>'