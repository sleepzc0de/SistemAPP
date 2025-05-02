import json
from app import db
from app.models.sbsk_validator import SBSKValidator

class SBSKService:
    """Service for managing SBSK validation rules"""
    
    def get_validator(self, asset_code):
        """
        Get or create SBSKValidator for an asset code
        
        Args:
            asset_code: Asset code to get validator for
            
        Returns:
            SBSKValidator object
        """
        # Check if validator exists
        validator = SBSKValidator.query.filter_by(asset_code=asset_code).first()
        
        if not validator:
            # Create new validator with default rules
            validator = SBSKValidator(asset_code)
            db.session.add(validator)
            db.session.commit()
        
        return validator
    
    def update_validation_rules(self, asset_code, rules):
        """
        Update validation rules for an asset code
        
        Args:
            asset_code: Asset code to update rules for
            rules: Dictionary with validation rules
            
        Returns:
            SBSKValidator object
        """
        # Get validator
        validator = self.get_validator(asset_code)
        
        # Update rules
        if isinstance(rules, dict):
            validator.validation_rules = json.dumps(rules)
        else:
            validator.validation_rules = rules
        
        db.session.commit()
        
        return validator
    
    def get_validation_rules(self, asset_code):
        """
        Get validation rules for an asset code
        
        Args:
            asset_code: Asset code to get rules for
            
        Returns:
            Dictionary with validation rules
        """
        # Get validator
        validator = self.get_validator(asset_code)
        
        # Parse rules
        if validator.validation_rules and isinstance(validator.validation_rules, str):
            return json.loads(validator.validation_rules)
        else:
            return validator.validation_rules
    
    def import_rules_from_pmk(self, pmk_file):
        """
        Import validation rules from PMK file
        
        Args:
            pmk_file: Path to PMK file (JSON format)
            
        Returns:
            Dictionary with import results
        """
        try:
            # Load PMK file
            with open(pmk_file, 'r') as f:
                pmk_data = json.load(f)
            
            # Process rules
            count = 0
            for item in pmk_data:
                asset_code = item.get('asset_code')
                rules = item.get('rules')
                
                if asset_code and rules:
                    # Update rules
                    self.update_validation_rules(asset_code, rules)
                    count += 1
            
            return {
                'success': True,
                'message': f'Successfully imported {count} rules from PMK file.',
                'count': count
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error importing rules from PMK file: {str(e)}',
                'count': 0
            }
    
    def get_sbsk_summary(self):
        """
        Get summary of all SBSK validation rules
        
        Returns:
            List of dictionaries with SBSK summary
        """
        # Get all validators
        validators = SBSKValidator.query.all()
        
        # Format summary
        summary = []
        for validator in validators:
            # Parse rules
            if validator.validation_rules and isinstance(validator.validation_rules, str):
                rules = json.loads(validator.validation_rules)
            else:
                rules = validator.validation_rules
            
            # Create summary item
            item = {
                'asset_code': validator.asset_code,
                'created_at': validator.created_at,
                'updated_at': validator.updated_at,
                'rule_count': len(rules) if isinstance(rules, dict) else 0
            }
            
            # Add specific rule summaries based on asset type
            if validator._is_building(validator.asset_code):
                item['asset_type'] = 'Building'
                item['building_type'] = rules.get('building_type', 'standard')
                item['max_units'] = rules.get('max_units', 1)
            elif validator._is_vehicle(validator.asset_code):
                item['asset_type'] = 'Vehicle'
                item['vehicle_type'] = rules.get('vehicle_type', 'operational')
                item['max_units'] = rules.get('max_units', 5)
            else:
                item['asset_type'] = 'Equipment'
                item['max_units'] = rules.get('max_units', 10)
            
            summary.append(item)
        
        return summary
    
    def get_sbsk_by_asset_type(self, asset_type=None):
        """
        Get SBSK rules grouped by asset type
        
        Args:
            asset_type: Optional asset type to filter by ('Building', 'Vehicle', 'Equipment')
            
        Returns:
            Dictionary with SBSK rules grouped by asset type
        """
        # Get all validators
        validators = SBSKValidator.query.all()
        
        # Group by asset type
        result = {
            'Building': [],
            'Vehicle': [],
            'Equipment': []
        }
        
        for validator in validators:
            # Parse rules
            if validator.validation_rules and isinstance(validator.validation_rules, str):
                rules = json.loads(validator.validation_rules)
            else:
                rules = validator.validation_rules
            
            # Determine asset type
            if validator._is_building(validator.asset_code):
                item_type = 'Building'
            elif validator._is_vehicle(validator.asset_code):
                item_type = 'Vehicle'
            else:
                item_type = 'Equipment'
            
            # Filter by asset type if specified
            if asset_type and item_type != asset_type:
                continue
            
            # Add to result
            result[item_type].append({
                'asset_code': validator.asset_code,
                'rules': rules
            })
        
        return result if not asset_type else result[asset_type]