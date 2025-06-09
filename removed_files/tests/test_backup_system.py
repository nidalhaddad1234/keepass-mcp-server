"""
Test backup system for KeePass MCP Server.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
import json
import gzip
import tempfile
import os
from datetime import datetime

from keepass_mcp_server.backup_manager import BackupManager
from keepass_mcp_server.exceptions import BackupError


class TestBackupManager:
    """Test cases for BackupManager."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock()
        config.keepass_db_path = "/test/database.kdbx"
        config.backup_count = 5
        config.get_backup_dir.return_value = Path("/test/backups")
        return config
    
    @pytest.fixture
    def backup_manager(self, mock_config):
        """Create BackupManager instance for testing."""
        with patch('keepass_mcp_server.backup_manager.Path.mkdir'):
            return BackupManager(mock_config)
    
    @pytest.fixture
    def temp_files(self):
        """Create temporary files for testing."""
        # Create temporary database file
        with tempfile.NamedTemporaryFile(suffix='.kdbx', delete=False) as db_file:
            db_file.write(b'mock database content')
            db_path = db_file.name
        
        # Create temporary backup directory
        backup_dir = tempfile.mkdtemp()
        
        yield db_path, backup_dir
        
        # Cleanup
        os.unlink(db_path)
        import shutil
        shutil.rmtree(backup_dir)
    
    def test_create_backup_success(self, backup_manager):
        """Test successful backup creation."""
        with patch('keepass_mcp_server.backup_manager.Path.exists', return_value=True), \
             patch('keepass_mcp_server.backup_manager.shutil.copy2') as mock_copy, \
             patch('keepass_mcp_server.backup_manager.Path.stat') as mock_stat, \
             patch.object(backup_manager, '_calculate_checksum', return_value='test_checksum'), \
             patch.object(backup_manager, '_verify_backup', return_value=True), \
             patch.object(backup_manager, '_save_backup_metadata'), \
             patch.object(backup_manager, '_cleanup_old_backups'):
            
            mock_stat.return_value.st_size = 1024
            
            result = backup_manager.create_backup(
                reason="manual",
                compress=False,
                verify=True
            )
            
            assert result['reason'] == "manual"
            assert result['compressed'] is False
            assert result['verified'] is True
            assert 'filename' in result
            assert 'created_at' in result
            mock_copy.assert_called_once()
    
    def test_create_compressed_backup(self, backup_manager):
        """Test compressed backup creation."""
        with patch('keepass_mcp_server.backup_manager.Path.exists', return_value=True), \
             patch.object(backup_manager, '_create_compressed_backup') as mock_compress, \
             patch('keepass_mcp_server.backup_manager.Path.stat') as mock_stat, \
             patch.object(backup_manager, '_calculate_checksum', return_value='test_checksum'), \
             patch.object(backup_manager, '_verify_backup', return_value=True), \
             patch.object(backup_manager, '_save_backup_metadata'), \
             patch.object(backup_manager, '_cleanup_old_backups'):
            
            mock_stat.return_value.st_size = 1024
            
            result = backup_manager.create_backup(
                reason="auto",
                compress=True,
                verify=True
            )
            
            assert result['compressed'] is True
            assert result['filename'].endswith('.gz')
            mock_compress.assert_called_once()
    
    def test_create_backup_database_not_found(self, backup_manager):
        """Test backup creation when database file doesn't exist."""
        with patch('keepass_mcp_server.backup_manager.Path.exists', return_value=False):
            with pytest.raises(BackupError, match="Database file not found"):
                backup_manager.create_backup()
    
    def test_create_backup_verification_failed(self, backup_manager):
        """Test backup creation when verification fails."""
        with patch('keepass_mcp_server.backup_manager.Path.exists', return_value=True), \
             patch('keepass_mcp_server.backup_manager.shutil.copy2'), \
             patch('keepass_mcp_server.backup_manager.Path.stat') as mock_stat, \
             patch.object(backup_manager, '_calculate_checksum', return_value='test_checksum'), \
             patch.object(backup_manager, '_verify_backup', return_value=False), \
             patch('keepass_mcp_server.backup_manager.Path.unlink') as mock_unlink:
            
            mock_stat.return_value.st_size = 1024
            
            with pytest.raises(BackupError, match="Backup verification failed"):
                backup_manager.create_backup(verify=True)
            
            mock_unlink.assert_called_once()  # Failed backup should be removed
    
    def test_restore_backup_success(self, backup_manager):
        """Test successful backup restoration."""
        mock_metadata = {
            'filename': 'test_backup.kdbx',
            'checksum': 'test_checksum',
            'compressed': False
        }
        
        with patch('keepass_mcp_server.backup_manager.Path.exists', return_value=True), \
             patch.object(backup_manager, '_load_backup_metadata', return_value=mock_metadata), \
             patch.object(backup_manager, '_verify_backup', return_value=True), \
             patch.object(backup_manager, 'create_backup') as mock_pre_backup, \
             patch('keepass_mcp_server.backup_manager.shutil.copy2') as mock_copy, \
             patch.object(backup_manager, '_calculate_checksum', return_value='test_checksum'):
            
            mock_pre_backup.return_value = {'filename': 'pre_restore_backup.kdbx'}
            
            result = backup_manager.restore_backup(
                'test_backup.kdbx',
                verify_before_restore=True,
                create_pre_restore_backup=True
            )
            
            assert result['backup_filename'] == 'test_backup.kdbx'
            assert 'pre_restore_backup' in result
            assert 'restored_at' in result
            mock_copy.assert_called()
    
    def test_restore_backup_not_found(self, backup_manager):
        """Test backup restoration when backup file doesn't exist."""
        with patch('keepass_mcp_server.backup_manager.Path.exists', return_value=False):
            with pytest.raises(BackupError, match="Backup file not found"):
                backup_manager.restore_backup('nonexistent_backup.kdbx')
    
    def test_restore_backup_verification_failed(self, backup_manager):
        """Test backup restoration when verification fails."""
        mock_metadata = {
            'filename': 'test_backup.kdbx',
            'checksum': 'test_checksum',
            'compressed': False
        }
        
        with patch('keepass_mcp_server.backup_manager.Path.exists', return_value=True), \
             patch.object(backup_manager, '_load_backup_metadata', return_value=mock_metadata), \
             patch.object(backup_manager, '_verify_backup', return_value=False):
            
            with pytest.raises(BackupError, match="Backup verification failed"):
                backup_manager.restore_backup('test_backup.kdbx', verify_before_restore=True)
    
    def test_restore_compressed_backup(self, backup_manager):
        """Test restoration of compressed backup."""
        mock_metadata = {
            'filename': 'test_backup.kdbx.gz',
            'checksum': 'test_checksum',
            'compressed': True
        }
        
        with patch('keepass_mcp_server.backup_manager.Path.exists', return_value=True), \
             patch.object(backup_manager, '_load_backup_metadata', return_value=mock_metadata), \
             patch.object(backup_manager, '_verify_backup', return_value=True), \
             patch.object(backup_manager, '_restore_compressed_backup') as mock_restore, \
             patch.object(backup_manager, '_calculate_checksum', return_value='test_checksum'), \
             patch('keepass_mcp_server.backup_manager.Path.unlink'):
            
            result = backup_manager.restore_backup('test_backup.kdbx.gz')
            
            assert result['backup_filename'] == 'test_backup.kdbx.gz'
            mock_restore.assert_called_once()
    
    def test_list_backups(self, backup_manager):
        """Test listing available backups."""
        mock_backups = [
            Mock(name='backup1.kdbx', stat=Mock(return_value=Mock(st_size=1024, st_mtime=1234567890))),
            Mock(name='backup2.kdbx.gz', stat=Mock(return_value=Mock(st_size=512, st_mtime=1234567891)))
        ]
        
        for backup in mock_backups:
            backup.suffix = '.kdbx'
            if backup.name.endswith('.gz'):
                backup.suffix = '.gz'
        
        with patch.object(backup_manager.backup_dir, 'glob', return_value=mock_backups), \
             patch.object(backup_manager, '_load_backup_metadata', return_value=None):
            
            results = backup_manager.list_backups(include_metadata=False)
            
            assert len(results) == 2
            assert results[0]['filename'] == 'backup1.kdbx'
            assert results[1]['filename'] == 'backup2.kdbx.gz'
            assert results[1]['compressed'] is True
    
    def test_list_backups_with_metadata(self, backup_manager):
        """Test listing backups with metadata."""
        mock_backup = Mock(name='backup1.kdbx')
        mock_backup.suffix = '.kdbx'
        mock_backup.stat.return_value.st_size = 1024
        mock_backup.stat.return_value.st_mtime = 1234567890
        
        mock_metadata = {
            'reason': 'manual',
            'compressed': False,
            'verified': True
        }
        
        with patch.object(backup_manager.backup_dir, 'glob', return_value=[mock_backup]), \
             patch.object(backup_manager, '_load_backup_metadata', return_value=mock_metadata):
            
            results = backup_manager.list_backups(include_metadata=True)
            
            assert len(results) == 1
            assert results[0]['reason'] == 'manual'
            assert results[0]['verified'] is True
    
    def test_delete_backup_success(self, backup_manager):
        """Test successful backup deletion."""
        with patch('keepass_mcp_server.backup_manager.Path.exists', return_value=True), \
             patch('keepass_mcp_server.backup_manager.Path.unlink') as mock_unlink:
            
            result = backup_manager.delete_backup('test_backup.kdbx')
            
            assert result is True
            assert mock_unlink.call_count >= 1  # Backup file and possibly metadata
    
    def test_delete_backup_not_found(self, backup_manager):
        """Test backup deletion when file doesn't exist."""
        with patch('keepass_mcp_server.backup_manager.Path.exists', return_value=False):
            with pytest.raises(BackupError, match="Backup file not found"):
                backup_manager.delete_backup('nonexistent.kdbx')
    
    def test_verify_backup_success(self, backup_manager):
        """Test successful backup verification."""
        mock_metadata = {
            'checksum': 'test_checksum',
            'original_size': 1024,
            'created_at': datetime.now().isoformat(),
            'reason': 'manual'
        }
        
        with patch('keepass_mcp_server.backup_manager.Path.exists', return_value=True), \
             patch.object(backup_manager, '_load_backup_metadata', return_value=mock_metadata), \
             patch.object(backup_manager, '_verify_backup', return_value=True), \
             patch('keepass_mcp_server.backup_manager.Path.stat') as mock_stat:
            
            mock_stat.return_value.st_size = 1024
            
            result = backup_manager.verify_backup('test_backup.kdbx')
            
            assert result['is_valid'] is True
            assert result['has_metadata'] is True
            assert result['checksum_match'] is True
            assert result['original_size'] == 1024
    
    def test_cleanup_old_backups(self, backup_manager):
        """Test cleanup of old backups."""
        # Create more backups than the limit
        mock_backups = []
        for i in range(7):  # More than the limit of 5
            backup = {
                'filename': f'backup_{i}.kdbx',
                'created_at': datetime.now(),
                'size': 1024
            }
            mock_backups.append(backup)
        
        with patch.object(backup_manager, 'list_backups', return_value=mock_backups), \
             patch.object(backup_manager, 'delete_backup', return_value=True) as mock_delete:
            
            deleted = backup_manager.cleanup_old_backups()
            
            assert len(deleted) == 2  # Should delete 2 oldest backups
            assert mock_delete.call_count == 2
    
    def test_get_backup_statistics(self, backup_manager):
        """Test backup statistics calculation."""
        mock_backups = [
            {
                'filename': 'backup1.kdbx',
                'size': 1024,
                'created_at': datetime.now(),
                'compressed': False,
                'reason': 'manual'
            },
            {
                'filename': 'backup2.kdbx.gz',
                'size': 512,
                'created_at': datetime.now(),
                'compressed': True,
                'reason': 'auto'
            }
        ]
        
        with patch.object(backup_manager, 'list_backups', return_value=mock_backups):
            stats = backup_manager.get_backup_statistics()
            
            assert stats['total_backups'] == 2
            assert stats['total_size'] == 1536  # 1024 + 512
            assert stats['compressed_count'] == 1
            assert stats['uncompressed_count'] == 1
            assert stats['backup_reasons']['manual'] == 1
            assert stats['backup_reasons']['auto'] == 1
    
    def test_get_backup_statistics_empty(self, backup_manager):
        """Test backup statistics with no backups."""
        with patch.object(backup_manager, 'list_backups', return_value=[]):
            stats = backup_manager.get_backup_statistics()
            
            assert stats['total_backups'] == 0
            assert stats['total_size'] == 0
            assert stats['oldest_backup'] is None
            assert stats['newest_backup'] is None
    
    def test_calculate_checksum(self, backup_manager, temp_files):
        """Test checksum calculation."""
        db_path, _ = temp_files
        
        checksum = backup_manager._calculate_checksum(Path(db_path))
        
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA256 hash length
    
    def test_create_compressed_backup_method(self, backup_manager, temp_files):
        """Test compressed backup creation method."""
        db_path, backup_dir = temp_files
        source_path = Path(db_path)
        backup_path = Path(backup_dir) / "test_backup.kdbx.gz"
        
        backup_manager._create_compressed_backup(source_path, backup_path)
        
        assert backup_path.exists()
        
        # Verify it's actually compressed
        with gzip.open(backup_path, 'rb') as f:
            content = f.read()
            assert content == b'mock database content'
    
    def test_restore_compressed_backup_method(self, backup_manager, temp_files):
        """Test compressed backup restoration method."""
        db_path, backup_dir = temp_files
        
        # Create compressed backup
        backup_path = Path(backup_dir) / "compressed_backup.kdbx.gz"
        with gzip.open(backup_path, 'wb') as f:
            f.write(b'compressed backup content')
        
        # Restore it
        restore_path = Path(backup_dir) / "restored.kdbx"
        backup_manager._restore_compressed_backup(backup_path, restore_path)
        
        assert restore_path.exists()
        with open(restore_path, 'rb') as f:
            content = f.read()
            assert content == b'compressed backup content'
    
    def test_verify_backup_compressed(self, backup_manager):
        """Test verification of compressed backup."""
        mock_compressed_data = b'mock compressed content'
        expected_checksum = backup_manager._calculate_checksum_from_data(mock_compressed_data)
        
        with patch('gzip.open', mock_open(read_data=mock_compressed_data)):
            result = backup_manager._verify_backup(
                Path('test.gz'),
                expected_checksum,
                is_compressed=True
            )
            
            assert result is True
    
    def test_verify_backup_uncompressed(self, backup_manager, temp_files):
        """Test verification of uncompressed backup."""
        db_path, _ = temp_files
        backup_path = Path(db_path)
        
        # Calculate expected checksum
        expected_checksum = backup_manager._calculate_checksum(backup_path)
        
        result = backup_manager._verify_backup(
            backup_path,
            expected_checksum,
            is_compressed=False
        )
        
        assert result is True
    
    def test_save_and_load_backup_metadata(self, backup_manager, temp_files):
        """Test saving and loading backup metadata."""
        _, backup_dir = temp_files
        backup_path = Path(backup_dir) / "test_backup.kdbx"
        
        metadata = {
            'filename': 'test_backup.kdbx',
            'created_at': '2024-01-01T00:00:00',
            'reason': 'test',
            'compressed': False,
            'verified': True
        }
        
        # Save metadata
        backup_manager._save_backup_metadata(backup_path, metadata)
        
        # Load metadata
        loaded_metadata = backup_manager._load_backup_metadata(backup_path)
        
        assert loaded_metadata == metadata
    
    def test_backup_metadata_load_failure(self, backup_manager):
        """Test handling of metadata load failure."""
        with patch('builtins.open', side_effect=FileNotFoundError):
            result = backup_manager._load_backup_metadata(Path('nonexistent.kdbx'))
            assert result is None
    
    def _calculate_checksum_from_data(self, data):
        """Helper method to calculate checksum from data."""
        import hashlib
        return hashlib.sha256(data).hexdigest()


class TestBackupManagerIntegration:
    """Integration tests for BackupManager with real file operations."""
    
    def test_full_backup_restore_cycle(self):
        """Test complete backup and restore cycle."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup paths
            db_path = Path(temp_dir) / "test.kdbx"
            backup_dir = Path(temp_dir) / "backups"
            backup_dir.mkdir()
            
            # Create test database file
            original_content = b"original database content"
            with open(db_path, 'wb') as f:
                f.write(original_content)
            
            # Setup config
            mock_config = Mock()
            mock_config.keepass_db_path = str(db_path)
            mock_config.backup_count = 5
            mock_config.get_backup_dir.return_value = backup_dir
            
            backup_manager = BackupManager(mock_config)
            
            # Create backup
            backup_info = backup_manager.create_backup(
                reason="test",
                compress=True,
                verify=True
            )
            
            assert backup_info['success'] is True
            assert backup_info['compressed'] is True
            assert backup_info['verified'] is True
            
            # Verify backup file exists
            backup_filename = backup_info['filename']
            backup_path = backup_dir / backup_filename
            assert backup_path.exists()
            
            # Modify original database
            modified_content = b"modified database content"
            with open(db_path, 'wb') as f:
                f.write(modified_content)
            
            # Restore from backup
            restore_info = backup_manager.restore_backup(
                backup_filename,
                verify_before_restore=True,
                create_pre_restore_backup=True
            )
            
            assert restore_info['backup_filename'] == backup_filename
            assert 'pre_restore_backup' in restore_info
            
            # Verify content was restored
            with open(db_path, 'rb') as f:
                restored_content = f.read()
                assert restored_content == original_content
    
    def test_backup_cleanup_integration(self):
        """Test backup cleanup with real files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_dir = Path(temp_dir)
            
            # Create mock config
            mock_config = Mock()
            mock_config.keepass_db_path = str(backup_dir / "test.kdbx")
            mock_config.backup_count = 3  # Keep only 3 backups
            mock_config.get_backup_dir.return_value = backup_dir
            
            backup_manager = BackupManager(mock_config)
            
            # Create 5 backup files
            backup_files = []
            for i in range(5):
                backup_file = backup_dir / f"backup_{i}.kdbx"
                with open(backup_file, 'w') as f:
                    f.write(f"backup content {i}")
                backup_files.append(backup_file)
            
            # Run cleanup
            with patch.object(backup_manager, 'list_backups') as mock_list:
                # Mock list_backups to return our files
                mock_backups = [
                    {
                        'filename': f.name,
                        'created_at': datetime.now(),
                        'size': 100
                    }
                    for f in backup_files
                ]
                mock_list.return_value = mock_backups
                
                deleted = backup_manager.cleanup_old_backups()
                
                # Should delete 2 oldest backups (5 - 3 = 2)
                assert len(deleted) == 2


if __name__ == "__main__":
    pytest.main([__file__])
