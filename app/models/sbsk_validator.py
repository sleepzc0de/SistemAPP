import json
from datetime import datetime
from app import db

class SBSKValidator(db.Model):
    """SBSK Validator model for validating asset requests against SBSK requirements"""
    __tablename__ = 'sbsk_validators'
    
    id = db.Column(db.Integer, primary_key=True)
    asset_code = db.Column(db.String(20), unique=True, index=True, nullable=False, comment="Kode Barang")
    validation_rules = db.Column(db.Text, nullable=False, comment="Aturan Validasi dalam format JSON")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, asset_code, validation_rules=None):
        self.asset_code = asset_code
        if validation_rules:
            self.validation_rules = json.dumps(validation_rules) if isinstance(validation_rules, dict) else validation_rules
        else:
            # Load default rules from the database or initialize with basic rules
            validator = SBSKValidator.query.filter_by(asset_code=asset_code).first()
            if validator:
                self.validation_rules = validator.validation_rules
            else:
                self.validation_rules = json.dumps(self._get_default_rules(asset_code))
    
    def validate_sbsk(self, asset_request):
        """Validate asset request against SBSK rules"""
        # Get satker data
        satker = asset_request.satker
        employee_count = satker.employee_count
        
        # Get existing assets
        existing_assets = satker.get_existing_assets(asset_request.asset_code)
        
        # Load validation rules
        rules = json.loads(self.validation_rules) if isinstance(self.validation_rules, str) else self.validation_rules
        
        # Initialize result
        result = {
            'approved': False,
            'confidence': 0.0,
            'details': {
                'sbsk_compliance': {
                    'met': False,
                    'description': ""
                },
                'existing_assets': {
                    'optimized': True,
                    'description': ""
                },
                'asset_condition': {
                    'description': ""
                }
            }
        }
        
        # Validate against SBSK
        if self._is_building(asset_request.asset_code):
            # Building validation
            sbsk_result = self._validate_building(rules, asset_request, satker, existing_assets)
        elif self._is_vehicle(asset_request.asset_code):
            # Vehicle validation
            sbsk_result = self._validate_vehicle(rules, asset_request, satker, existing_assets)
        else:
            # General validation
            sbsk_result = self._validate_general(rules, asset_request, satker, existing_assets)
        
        # Update result with SBSK validation
        result['details']['sbsk_compliance'] = sbsk_result
        
        # Check if existing assets are optimized
        optimization_result = self._check_asset_optimization(existing_assets)
        result['details']['existing_assets'] = optimization_result
        
        # Check asset conditions
        condition_result = self._check_asset_conditions(existing_assets)
        result['details']['asset_condition'] = condition_result
        
        # Calculate final result
        if sbsk_result['met'] and optimization_result['optimized']:
            result['approved'] = True
            result['confidence'] = 0.9  # High confidence if all checks pass
        elif sbsk_result['met'] and not optimization_result['optimized']:
            result['approved'] = False
            result['confidence'] = 0.7  # Medium confidence
        else:
            result['approved'] = False
            result['confidence'] = 0.8  # High confidence for rejection due to SBSK violation
        
        return result
    
    def check_percentage(self, current, maximum):
        """Check what percentage of maximum is represented by current value"""
        if maximum == 0:
            return 0
        return (current / maximum) * 100
    
    def validate_requirements(self, requirements, asset_request):
        """Validate specific requirements"""
        # This method would implement validation against specific requirements
        # To be implemented with detailed business logic
        return True
    
    def _is_building(self, asset_code):
        """Check if asset is a building"""
        return asset_code.startswith('03')
    
    def _is_vehicle(self, asset_code):
        """Check if asset is a vehicle"""
        return asset_code.startswith('02') and asset_code[2:4] in ['01', '02', '03']
    
    def _validate_building(self, rules, asset_request, satker, existing_assets):
        """Validate building requests against SBSK"""
        employee_count = satker.employee_count
        request_quantity = asset_request.request_quantity
        
        # Get building type from rules
        building_type = rules.get('building_type', 'standard')
        
        # SBSK for buildings is typically based on employee count and building type
        if building_type == 'kantor':
            # Office building
            max_area_per_employee = 9  # 9 m² per employee based on PMK 138/2024
            if 'max_area' in rules:
                max_area = rules['max_area']
            else:
                max_area = employee_count * max_area_per_employee
            
            # Assuming request_quantity represents area in m²
            if request_quantity <= max_area:
                return {
                    'met': True,
                    'description': f"Luas yang diusulkan ({request_quantity} m²) sesuai dengan standar (max: {max_area} m²)."
                }
            else:
                return {
                    'met': False,
                    'max_allowed': max_area,
                    'description': f"Luas yang diusulkan ({request_quantity} m²) melebihi standar (max: {max_area} m²)."
                }
        else:
            # Other building types
            if 'max_units' in rules:
                max_units = rules['max_units']
                if request_quantity <= max_units:
                    return {
                        'met': True,
                        'description': f"Jumlah bangunan yang diusulkan ({request_quantity} unit) sesuai dengan standar (max: {max_units} unit)."
                    }
                else:
                    return {
                        'met': False,
                        'max_allowed': max_units,
                        'description': f"Jumlah bangunan yang diusulkan ({request_quantity} unit) melebihi standar (max: {max_units} unit)."
                    }
            else:
                # Default check
                if request_quantity <= 1:
                    return {
                        'met': True,
                        'description': "Jumlah bangunan yang diusulkan sesuai dengan standar default."
                    }
                else:
                    return {
                        'met': False,
                        'max_allowed': 1,
                        'description': "Jumlah bangunan yang diusulkan melebihi standar default."
                    }
    
    def _validate_vehicle(self, rules, asset_request, satker, existing_assets):
        """Validate vehicle requests against SBSK"""
        employee_count = satker.employee_count
        request_quantity = asset_request.request_quantity
        
        # Get vehicle type from rules
        vehicle_type = rules.get('vehicle_type', 'operational')
        
        # Count existing vehicles of this type
        existing_count = len(existing_assets)
        
        # SBSK for vehicles is typically based on employee count and vehicle type
        if vehicle_type == 'operasional':
            # Operational vehicles
            # Based on PMK 138/2024, 1 operational vehicle per 5 structural officials
            # Assuming 20% of employees are structural officials
            structural_officials = int(employee_count * 0.2)
            max_vehicles = max(1, structural_officials // 5)
            
            # Consider existing vehicles
            max_additional = max(0, max_vehicles - existing_count)
            
            if request_quantity <= max_additional:
                return {
                    'met': True,
                    'description': f"Jumlah kendaraan yang diusulkan ({request_quantity} unit) sesuai dengan standar (max tambahan: {max_additional} unit)."
                }
            else:
                return {
                    'met': False,
                    'max_allowed': max_additional,
                    'description': f"Jumlah kendaraan yang diusulkan ({request_quantity} unit) melebihi standar (max tambahan: {max_additional} unit)."
                }
        elif vehicle_type == 'pejabat':
            # For officials
            # Check if requester is eligible for official vehicle
            # This would require additional logic to check user role/position
            if 'is_eligible' in rules and rules['is_eligible']:
                # Check if already has a vehicle
                if existing_count == 0:
                    if request_quantity <= 1:
                        return {
                            'met': True,
                            'description': "Pejabat berhak mendapatkan 1 kendaraan dinas."
                        }
                    else:
                        return {
                            'met': False,
                            'max_allowed': 1,
                            'description': "Pejabat hanya berhak mendapatkan 1 kendaraan dinas."
                        }
                else:
                    return {
                        'met': False,
                        'max_allowed': 0,
                        'description': "Pejabat sudah memiliki kendaraan dinas."
                    }
            else:
                return {
                    'met': False,
                    'max_allowed': 0,
                    'description': "Tidak berhak mendapatkan kendaraan dinas pejabat."
                }
        else:
            # Other vehicle types
            if 'max_units' in rules:
                max_units = rules['max_units']
                max_additional = max(0, max_units - existing_count)
                
                if request_quantity <= max_additional:
                    return {
                        'met': True,
                        'description': f"Jumlah kendaraan yang diusulkan ({request_quantity} unit) sesuai dengan standar (max tambahan: {max_additional} unit)."
                    }
                else:
                    return {
                        'met': False,
                        'max_allowed': max_additional,
                        'description': f"Jumlah kendaraan yang diusulkan ({request_quantity} unit) melebihi standar (max tambahan: {max_additional} unit)."
                    }
            else:
                # Default check based on employee count
                default_max = max(1, employee_count // 20)  # 1 vehicle per 20 employees
                max_additional = max(0, default_max - existing_count)
                
                if request_quantity <= max_additional:
                    return {
                        'met': True,
                        'description': f"Jumlah kendaraan yang diusulkan ({request_quantity} unit) sesuai dengan standar default (max tambahan: {max_additional} unit)."
                    }
                else:
                    return {
                        'met': False,
                        'max_allowed': max_additional,
                        'description': f"Jumlah kendaraan yang diusulkan ({request_quantity} unit) melebihi standar default (max tambahan: {max_additional} unit)."
                    }
    
    def _validate_general(self, rules, asset_request, satker, existing_assets):
        """Validate general equipment requests against SBSK"""
        employee_count = satker.employee_count
        request_quantity = asset_request.request_quantity
        
        # Count existing assets of this type
        existing_count = len(existing_assets)
        
        # Get equipment type from asset code
        asset_code = asset_request.asset_code
        
        # Special handling for computers and printers
        if asset_code.startswith('0201'):  # Assume 0201 is for computers
            # Based on PMK 138/2024, typically 1 computer per employee
            max_units = employee_count
            max_additional = max(0, max_units - existing_count)
            
            if request_quantity <= max_additional:
                return {
                    'met': True,
                    'description': f"Jumlah komputer yang diusulkan ({request_quantity} unit) sesuai dengan standar (max tambahan: {max_additional} unit)."
                }
            else:
                return {
                    'met': False,
                    'max_allowed': max_additional,
                    'description': f"Jumlah komputer yang diusulkan ({request_quantity} unit) melebihi standar (max tambahan: {max_additional} unit)."
                }
        elif asset_code.startswith('0202'):  # Assume 0202 is for printers
            # Based on PMK 138/2024, typically 1 printer per 5 employees
            max_units = max(1, employee_count // 5)
            max_additional = max(0, max_units - existing_count)
            
            if request_quantity <= max_additional:
                return {
                    'met': True,
                    'description': f"Jumlah printer yang diusulkan ({request_quantity} unit) sesuai dengan standar (max tambahan: {max_additional} unit)."
                }
            else:
                return {
                    'met': False,
                    'max_allowed': max_additional,
                    'description': f"Jumlah printer yang diusulkan ({request_quantity} unit) melebihi standar (max tambahan: {max_additional} unit)."
                }
        else:
            # General equipment
            if 'max_units' in rules:
                max_units = rules['max_units']
                max_additional = max(0, max_units - existing_count)
                
                if request_quantity <= max_additional:
                    return {
                        'met': True,
                        'description': f"Jumlah yang diusulkan ({request_quantity} unit) sesuai dengan standar (max tambahan: {max_additional} unit)."
                    }
                else:
                    return {
                        'met': False,
                        'max_allowed': max_additional,
                        'description': f"Jumlah yang diusulkan ({request_quantity} unit) melebihi standar (max tambahan: {max_additional} unit)."
                    }
            else:
                # Default check - 1 per department
                # Assuming 1 department per 10 employees
                departments = max(1, employee_count // 10)
                default_max = departments
                max_additional = max(0, default_max - existing_count)
                
                if request_quantity <= max_additional:
                    return {
                        'met': True,
                        'description': f"Jumlah yang diusulkan ({request_quantity} unit) sesuai dengan standar default (max tambahan: {max_additional} unit)."
                    }
                else:
                    return {
                        'met': False,
                        'max_allowed': max_additional,
                        'description': f"Jumlah yang diusulkan ({request_quantity} unit) melebihi standar default (max tambahan: {max_additional} unit)."
                    }
    
    def _check_asset_optimization(self, existing_assets):
        """Check if existing assets are optimized"""
        # Count assets by condition
        good_condition = 0
        minor_damage = 0
        major_damage = 0
        
        for asset in existing_assets:
            if asset.asset_condition == 'Baik':
                good_condition += 1
            elif asset.asset_condition == 'Rusak Ringan':
                minor_damage += 1
            elif asset.asset_condition == 'Rusak Berat':
                major_damage += 1
        
        # Check if there are idle assets in good condition
        if good_condition > 0:
            return {
                'optimized': False,
                'description': f"Terdapat {good_condition} aset dalam kondisi baik yang dapat dimanfaatkan."
            }
        
        # Check if there are assets with minor damage that can be repaired
        if minor_damage > 0:
            return {
                'optimized': False,
                'description': f"Terdapat {minor_damage} aset dengan kerusakan ringan yang dapat diperbaiki."
            }
        
        return {
            'optimized': True,
            'description': "Semua aset yang ada telah dioptimalkan."
        }
    
    def _check_asset_conditions(self, existing_assets):
        """Check conditions of existing assets"""
        # Count assets by condition
        total = len(existing_assets)
        good_condition = 0
        minor_damage = 0
        major_damage = 0
        
        for asset in existing_assets:
            if asset.asset_condition == 'Baik':
                good_condition += 1
            elif asset.asset_condition == 'Rusak Ringan':
                minor_damage += 1
            elif asset.asset_condition == 'Rusak Berat':
                major_damage += 1
        
        # Calculate percentages
        good_percentage = (good_condition / total) * 100 if total > 0 else 0
        minor_damage_percentage = (minor_damage / total) * 100 if total > 0 else 0
        major_damage_percentage = (major_damage / total) * 100 if total > 0 else 0
        
        # Format condition description
        description = f"Total aset: {total}. "
        
        if total > 0:
            description += f"Kondisi baik: {good_condition} ({good_percentage:.1f}%), "
            description += f"Rusak ringan: {minor_damage} ({minor_damage_percentage:.1f}%), "
            description += f"Rusak berat: {major_damage} ({major_damage_percentage:.1f}%)."
        else:
            description += "Belum memiliki aset jenis ini."
        
        return {
            'description': description
        }
    
    def _get_default_rules(self, asset_code):
        """Get default rules based on asset code"""
        # Create rules based on asset type
        if self._is_building(asset_code):
            # Building rules
            rules = {
                'building_type': 'standard',
                'max_units': 1,
                'standards': {
                    'height': {'min': 3, 'max': 4, 'unit': 'm'},
                    'area_per_employee': {'value': 9, 'unit': 'm²'}
                }
            }
        elif self._is_vehicle(asset_code):
            # Vehicle rules
            rules = {
                'vehicle_type': 'operational',
                'max_units': 5,
                'standards': {
                    'replacement_age': {'value': 10, 'unit': 'tahun'},
                    'replacement_distance': {'value': 150000, 'unit': 'km'}
                }
            }
        else:
            # General equipment rules
            rules = {
                'max_units': 10,
                'standards': {
                    'replacement_age': {'value': 5, 'unit': 'tahun'}
                }
            }
        
        return rules
    
    def __repr__(self):
        return f'<SBSKValidator {self.asset_code}>'
 of this type
        existing_count = len(existing_assets)
        
        # Get equipment type from asset code
        asset_code = asset_request.asset_code
        
        # Special handling for computers and printers
        if asset_code.startswith('0201'):  # Assume 0201 is for computers
            # Based on PMK 138/2024, typically 1 computer per employee
            max_units = employee_count
            max_additional = max(0, max_units - existing_count)
            
            if request_quantity <= max_additional:
                return {
                    'met': True,
                    'description': f"Jumlah komputer yang diusulkan ({request_quantity} unit) sesuai dengan standar (max tambahan: {max_additional} unit)."
                }
            else:
                return {
                    'met': False,
                    'max_allowed': max_additional,
                    'description': f"Jumlah komputer yang diusulkan ({request_quantity} unit) melebihi standar (max tambahan: {max_additional} unit)."
                }
        elif asset_code.startswith('0202'):  # Assume 0202 is for printers
            # Based on PMK 138/2024, typically 1 printer per 5 employees
            max_units = max(1, employee_count // 5)
            max_additional = max(0, max_units - existing_count)
            
            if request_quantity <= max_additional:
                return {
                    'met': True,
                    'description': f"Jumlah printer yang diusulkan ({request_quantity} unit) sesuai dengan standar (max tambahan: {max_additional} unit)."
                }
            else:
                return {
                    'met': False,
                    'max_allowed': max_additional,
                    'description': f"Jumlah printer yang diusulkan ({request_quantity} unit) melebihi standar (max tambahan: {max_additional} unit)."
                }
        else:
            # General equipment
            if 'max_units' in rules:
                max_units = rules['max_units']
                max_additional = max(0, max_units - existing_count)
                
                if request_quantity <= max_additional:
                    return {
                        'met': True,
                        'description': f"Jumlah yang diusulkan ({request_quantity} unit) sesuai dengan standar (max tambahan: {max_additional} unit)."
                    }
                else:
                    return {
                        'met': False,
                        'max_allowed': max_additional,
                        'description': f"Jumlah yang diusulkan ({request_quantity} unit) melebihi standar (max tambahan: {max_additional} unit)."
                    }
            else:
                # Default check - 1 per department
                # Assuming 1 department per 10 employees
                departments = max(1, employee_count // 10)
                default_max = departments
                max_additional = max(0, default_max - existing_count)
                
                if request_quantity <= max_additional:
                    return {
                        'met': True,
                        'description': f"Jumlah yang diusulkan ({request_quantity} unit) sesuai dengan standar default (max tambahan: {max_additional} unit)."
                    }
                else:
                    return {
                        'met': False,
                        'max_allowed': max_additional,
                        'description': f"Jumlah yang diusulkan ({request_quantity} unit) melebihi standar default (max tambahan: {max_additional} unit)."
                    }
    
    def _check_asset_optimization(self, existing_assets):
        """Check if existing assets are optimized"""
        # Count assets by condition
        good_condition = 0
        minor_damage = 0
        major_damage = 0
        
        for asset in existing_assets:
            if asset.asset_condition == 'Baik':
                good_condition += 1
            elif asset.asset_condition == 'Rusak Ringan':
                minor_damage += 1
            elif asset.asset_condition == 'Rusak Berat':
                major_damage += 1
        
        # Check if there are idle assets in good condition
        if good_condition > 0:
            return {
                'optimized': False,
                'description': f"Terdapat {good_condition} aset dalam kondisi baik yang dapat dimanfaatkan."
            }
        
        # Check if there are assets with minor damage that can be repaired
        if minor_damage > 0:
            return {
                'optimized': False,
                'description': f"Terdapat {minor_damage} aset dengan kerusakan ringan yang dapat diperbaiki."
            }
        
        return {
            'optimized': True,
            'description': "Semua aset yang ada telah dioptimalkan."
        }
    
    def _check_asset_conditions(self, existing_assets):
        """Check conditions of existing assets"""
        # Count assets by condition
        total = len(existing_assets)
        good_condition = 0
        minor_damage = 0
        major_damage = 0
        
        for asset in existing_assets:
            if asset.asset_condition == 'Baik':
                good_condition += 1
            elif asset.asset_condition == 'Rusak Ringan':
                minor_damage += 1