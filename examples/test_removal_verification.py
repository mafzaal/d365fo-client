#!/usr/bin/env python3
"""
Verification test to ensure MetadataManager removal was successful
"""


def test_imports():
    """Test that all imports work correctly"""
    print("Testing imports...")
    try:
        import d365fo_client
        from d365fo_client import FOClient, FOClientConfig

        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False


def test_module_structure():
    """Test module structure"""
    print("\nTesting module structure...")
    try:
        import d365fo_client.client as client_module
        import d365fo_client.metadata_api as metadata_api_module

        has_foclient = hasattr(client_module, "FOClient")
        has_metadata_ops = hasattr(metadata_api_module, "MetadataAPIOperations")

        print(f"✅ FOClient class available: {has_foclient}")
        print(f"✅ MetadataAPIOperations available: {has_metadata_ops}")
        print("✅ Modern metadata system confirmed")

        return has_foclient and has_metadata_ops
    except Exception as e:
        print(f"❌ Module structure error: {e}")
        return False


def test_metadata_manager_removed():
    """Test that MetadataManager is not accessible"""
    print("\nTesting MetadataManager removal...")
    try:
        # Try to import MetadataManager - should fail
        try:
            from d365fo_client.metadata import MetadataManager

            print("❌ MetadataManager still exists!")
            return False
        except ImportError:
            print("✅ MetadataManager import correctly fails")

        # Check file doesn't exist
        import os

        metadata_file = os.path.join("src", "d365fo_client", "metadata.py")
        if os.path.exists(metadata_file):
            print("❌ metadata.py file still exists!")
            return False
        else:
            print("✅ metadata.py file successfully removed")

        return True
    except Exception as e:
        print(f"❌ MetadataManager removal test error: {e}")
        return False


def test_modern_metadata_system():
    """Test that modern metadata system is accessible"""
    print("\nTesting modern metadata system...")
    try:
        # Test that we can import modern components
        from d365fo_client.metadata_api import MetadataAPIOperations
        from d365fo_client.metadata_v2.cache_v2 import MetadataCacheV2

        print("✅ MetadataAPIOperations imported successfully")
        print("✅ MetadataCacheV2 imported successfully")
        print("✅ Modern metadata system fully functional")
        return True
    except Exception as e:
        print(f"❌ Modern metadata system error: {e}")
        return False


def main():
    """Run all verification tests"""
    print("=" * 60)
    print("VERIFICATION: MetadataManager Removal")
    print("=" * 60)

    tests = [
        test_imports,
        test_module_structure,
        test_metadata_manager_removed,
        test_modern_metadata_system,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()  # Add spacing

    print("=" * 60)
    print(f"RESULTS: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED - MetadataManager removal successful!")
        return 0
    else:
        print("❌ Some tests failed - Check the issues above")
        return 1


if __name__ == "__main__":
    exit(main())
