#!/usr/bin/env python3
"""
Download and Convert Real Training Datasets
===========================================
Downloads publicly available syscall anomaly detection datasets and converts
them to the format expected by the agent.

Supported Datasets:
1. ADFA-LD (Australian Defence Force Academy Linux Dataset)
2. DongTing Dataset (if available)
3. Other public datasets

Author: Likitha Shankar
"""

import sys
import os
import json
import argparse
import requests
import zipfile
import tarfile
from pathlib import Path
from typing import List, Tuple, Dict, Any
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def download_file(url: str, output_path: Path, chunk_size: int = 8192) -> bool:
    """Download a file from URL"""
    try:
        print(f"📥 Downloading from {url}...")
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r   Progress: {percent:.1f}%", end='', flush=True)
        
        print(f"\n✅ Downloaded to {output_path}")
        return True
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False

def extract_archive(archive_path: Path, extract_to: Path) -> bool:
    """Extract zip or tar archive"""
    try:
        print(f"📦 Extracting {archive_path.name}...")
        extract_to.mkdir(parents=True, exist_ok=True)
        
        if archive_path.suffix == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
        elif archive_path.suffix in ['.tar', '.gz', '.bz2'] or '.tar.' in archive_path.name:
            with tarfile.open(archive_path, 'r:*') as tar_ref:
                tar_ref.extractall(extract_to)
        else:
            print(f"⚠️  Unknown archive format: {archive_path.suffix}")
            return False
        
        print(f"✅ Extracted to {extract_to}")
        return True
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return False

def get_syscall_number_to_name_map() -> Dict[int, str]:
    """Get complete syscall number to name mapping for x86_64"""
    return {
        0: 'read', 1: 'write', 2: 'open', 3: 'close', 4: 'stat',
        5: 'fstat', 6: 'lstat', 7: 'poll', 8: 'lseek', 9: 'mmap',
        10: 'mprotect', 11: 'munmap', 12: 'brk', 13: 'rt_sigaction',
        14: 'rt_sigprocmask', 15: 'rt_sigreturn', 16: 'ioctl', 17: 'pread64',
        18: 'pwrite64', 19: 'readv', 20: 'writev', 21: 'access',
        22: 'pipe', 23: 'select', 24: 'sched_yield', 25: 'mremap',
        26: 'msync', 27: 'mincore', 28: 'madvise', 29: 'shmget',
        30: 'shmat', 31: 'shmctl', 32: 'dup', 33: 'dup2', 34: 'pause',
        35: 'nanosleep', 36: 'getitimer', 37: 'alarm', 38: 'setitimer',
        39: 'getpid', 40: 'sendfile', 41: 'socket', 42: 'connect',
        43: 'accept', 44: 'sendto', 45: 'recvfrom', 46: 'sendmsg',
        47: 'recvmsg', 48: 'shutdown', 49: 'bind', 50: 'listen',
        51: 'getsockname', 52: 'getpeername', 53: 'socketpair', 54: 'setsockopt',
        55: 'getsockopt', 56: 'clone', 57: 'fork', 58: 'vfork', 59: 'execve',
        60: 'exit', 61: 'wait4', 62: 'kill', 63: 'uname', 64: 'semget',
        65: 'semop', 66: 'semctl', 67: 'shmdt', 68: 'msgget', 69: 'msgsnd',
        70: 'msgrcv', 71: 'msgctl', 72: 'fcntl', 73: 'flock', 74: 'fsync',
        75: 'fdatasync', 76: 'truncate', 77: 'ftruncate', 78: 'getdents',
        79: 'getcwd', 80: 'chdir', 81: 'fchdir', 82: 'rename', 83: 'mkdir',
        84: 'rmdir', 85: 'creat', 86: 'link', 87: 'unlink', 88: 'symlink',
        89: 'readlink', 90: 'chmod', 91: 'fchmod', 92: 'chown', 93: 'fchown',
        94: 'lchown', 95: 'umask', 96: 'gettimeofday', 97: 'getrlimit',
        98: 'getrusage', 99: 'sysinfo', 100: 'times', 101: 'ptrace',
        102: 'getuid', 103: 'syslog', 104: 'getgid', 105: 'setuid',
        106: 'setgid', 107: 'geteuid', 108: 'getegid', 109: 'setpgid',
        110: 'getppid', 111: 'getpgrp', 112: 'setsid', 113: 'setreuid',
        114: 'setregid', 115: 'getgroups', 116: 'setgroups', 117: 'setresuid',
        118: 'getresuid', 119: 'setresgid', 120: 'getresgid', 121: 'getpgid',
        122: 'setfsuid', 123: 'setfsgid', 124: 'getsid', 125: 'capget',
        126: 'capset', 127: 'rt_sigpending', 128: 'rt_sigtimedwait',
        129: 'rt_sigqueueinfo', 130: 'rt_sigsuspend', 131: 'sigaltstack',
        132: 'utime', 133: 'mknod', 134: 'uselib', 135: 'personality',
        136: 'ustat', 137: 'statfs', 138: 'fstatfs', 139: 'sysfs',
        140: 'getpriority', 141: 'setpriority', 142: 'sched_setparam',
        143: 'sched_getparam', 144: 'sched_setscheduler', 145: 'sched_getscheduler',
        146: 'sched_get_priority_max', 147: 'sched_get_priority_min',
        148: 'sched_rr_get_interval', 149: 'mlock', 150: 'munlock',
        151: 'mlockall', 152: 'munlockall', 153: 'vhangup', 154: 'modify_ldt',
        155: 'pivot_root', 156: 'prctl', 157: 'arch_prctl', 158: 'adjtimex',
        159: 'setrlimit', 160: 'chroot', 161: 'sync', 162: 'acct', 163: 'settimeofday',
        164: 'mount', 165: 'umount2', 166: 'swapon', 167: 'swapoff',
        168: 'reboot', 169: 'sethostname', 170: 'setdomainname', 171: 'iopl',
        172: 'ioperm', 173: 'create_module', 174: 'init_module', 175: 'delete_module',
        176: 'get_kernel_syms', 177: 'query_module', 178: 'quotactl', 179: 'nfsservctl',
        180: 'getpmsg', 181: 'putpmsg', 182: 'afs_syscall', 183: 'tuxcall',
        184: 'security', 185: 'gettid', 186: 'readahead', 187: 'setxattr',
        188: 'lsetxattr', 189: 'fsetxattr', 190: 'getxattr', 191: 'lgetxattr',
        192: 'fgetxattr', 193: 'listxattr', 194: 'llistxattr', 195: 'flistxattr',
        196: 'removexattr', 197: 'lremovexattr', 198: 'fremovexattr', 199: 'tkill',
        200: 'time', 201: 'futex', 202: 'sched_setaffinity', 203: 'sched_getaffinity',
        204: 'set_thread_area', 205: 'io_setup', 206: 'io_destroy', 207: 'io_getevents',
        208: 'io_submit', 209: 'io_cancel', 210: 'get_thread_area',
        211: 'lookup_dcookie', 212: 'epoll_create', 213: 'epoll_ctl_old',
        214: 'epoll_wait_old', 215: 'remap_file_pages', 216: 'getdents64',
        217: 'set_tid_address', 218: 'restart_syscall', 219: 'semtimedop',
        220: 'fadvise64', 221: 'timer_create', 222: 'timer_settime', 223: 'timer_gettime',
        224: 'timer_getoverrun', 225: 'timer_delete', 226: 'clock_settime',
        227: 'clock_gettime', 228: 'clock_getres', 229: 'clock_nanosleep',
        230: 'exit_group', 231: 'epoll_wait', 232: 'epoll_ctl', 233: 'tgkill',
        234: 'utimes', 235: 'vserver', 236: 'mbind', 237: 'set_mempolicy',
        238: 'get_mempolicy', 239: 'mq_open', 240: 'mq_unlink', 241: 'mq_timedsend',
        242: 'mq_timedreceive', 243: 'mq_notify', 244: 'mq_getsetattr',
        245: 'kexec_load', 246: 'waitid', 247: 'add_key', 248: 'request_key',
        249: 'keyctl', 250: 'ioprio_set', 251: 'ioprio_get', 252: 'inotify_init',
        253: 'inotify_add_watch', 254: 'inotify_rm_watch', 255: 'migrate_pages',
        256: 'openat', 257: 'mkdirat', 258: 'mknodat', 259: 'fchownat',
        260: 'futimesat', 261: 'newfstatat', 262: 'unlinkat', 263: 'renameat',
        264: 'linkat', 265: 'symlinkat', 266: 'readlinkat', 267: 'fchmodat',
        268: 'faccessat', 269: 'pselect6', 270: 'ppoll', 271: 'unshare',
        272: 'set_robust_list', 273: 'get_robust_list', 274: 'splice',
        275: 'tee', 276: 'sync_file_range', 277: 'vmsplice', 278: 'move_pages',
        279: 'utimensat', 280: 'epoll_pwait', 281: 'signalfd', 282: 'timerfd',
        283: 'eventfd', 284: 'fallocate', 285: 'timerfd_settime', 286: 'timerfd_gettime',
        287: 'accept4', 288: 'signalfd4', 289: 'eventfd2', 290: 'epoll_create1',
        291: 'dup3', 292: 'pipe2', 293: 'inotify_init1', 294: 'preadv',
        295: 'pwritev', 296: 'rt_tgsigqueueinfo', 297: 'perf_event_open',
        298: 'recvmmsg', 299: 'fanotify_init', 300: 'fanotify_mark',
        301: 'prlimit64', 302: 'name_to_handle_at', 303: 'open_by_handle_at',
        304: 'clock_adjtime', 305: 'syncfs', 306: 'sendmmsg', 307: 'setns',
        308: 'getcpu', 309: 'process_vm_readv', 310: 'process_vm_writev',
        311: 'kcmp', 312: 'finit_module', 313: 'sched_setattr', 314: 'sched_getattr',
        315: 'renameat2', 316: 'seccomp', 317: 'getrandom', 318: 'memfd_create',
        319: 'kexec_file_load', 320: 'bpf', 321: 'execveat', 322: 'userfaultfd',
        323: 'membarrier', 324: 'mlock2', 325: 'copy_file_range', 326: 'preadv2',
        327: 'pwritev2', 328: 'pkey_mprotect', 329: 'pkey_alloc', 330: 'pkey_free',
        331: 'statx', 332: 'io_pgetevents', 333: 'rseq'
    }

def convert_adfa_ld_format(adfa_dir: Path) -> List[Tuple[List[str], Dict]]:
    """
    Convert ADFA-LD dataset format to our training data format
    
    ADFA-LD structure:
    - Training_Data_Master/ (normal sequences)
    - Validation_Data_Master/ (normal sequences)
    - Attack_Data_Master/ (attack sequences)
    
    ADFA-LD stores syscalls as numbers (one per line), we convert to names.
    """
    training_data = []
    syscall_map = get_syscall_number_to_name_map()
    unmapped_count = 0
    total_syscalls = 0
    
    def convert_syscall_numbers_to_names(syscall_numbers: List[str]) -> List[str]:
        """Convert list of syscall number strings to syscall name strings"""
        nonlocal unmapped_count, total_syscalls
        syscall_names = []
        for num_str in syscall_numbers:
            total_syscalls += 1
            try:
                num = int(num_str.strip())
                name = syscall_map.get(num, f'syscall_{num}')
                if name.startswith('syscall_'):
                    unmapped_count += 1
                syscall_names.append(name)
            except ValueError:
                # If it's already a name or invalid, keep as-is
                syscall_names.append(num_str.strip())
        return syscall_names
    
    # Process normal sequences
    normal_dirs = ['Training_Data_Master', 'Validation_Data_Master']
    for dir_name in normal_dirs:
        normal_dir = adfa_dir / dir_name
        if not normal_dir.exists():
            continue
        
        print(f"📂 Processing {dir_name}...")
        for file_path in normal_dir.glob('*.txt'):
            try:
                with open(file_path, 'r') as f:
                    # ADFA-LD format: all syscall numbers on one line, space-separated
                    content = f.read().strip()
                    # Split by spaces to get individual syscall numbers
                    syscall_numbers = [num.strip() for num in content.split() if num.strip()]
                
                if syscall_numbers:
                    # Convert syscall numbers to names
                    syscalls = convert_syscall_numbers_to_names(syscall_numbers)
                    
                    process_info = {
                        'cpu_percent': 10.0,  # Default values
                        'memory_percent': 5.0,
                        'num_threads': 1,
                        'pid': 0,
                        'source': 'ADFA-LD',
                        'label': 'normal'
                    }
                    training_data.append((syscalls, process_info))
            except Exception as e:
                print(f"⚠️  Error processing {file_path}: {e}")
    
    # Process attack sequences (for evaluation, not training)
    attack_dir = adfa_dir / 'Attack_Data_Master'
    if attack_dir.exists():
        print(f"📂 Processing Attack_Data_Master (for evaluation)...")
        attack_count = 0
        for file_path in attack_dir.glob('*.txt'):
            try:
                with open(file_path, 'r') as f:
                    # ADFA-LD format: all syscall numbers on one line, space-separated
                    content = f.read().strip()
                    # Split by spaces to get individual syscall numbers
                    syscall_numbers = [num.strip() for num in content.split() if num.strip()]
                
                if syscall_numbers:
                    # Convert syscall numbers to names
                    syscalls = convert_syscall_numbers_to_names(syscall_numbers)
                    
                    process_info = {
                        'cpu_percent': 15.0,
                        'memory_percent': 8.0,
                        'num_threads': 1,
                        'pid': 0,
                        'source': 'ADFA-LD',
                        'label': 'attack'
                    }
                    training_data.append((syscalls, process_info))
                    attack_count += 1
            except Exception as e:
                print(f"⚠️  Error processing {file_path}: {e}")
        
        print(f"   Found {attack_count} attack sequences (for evaluation)")
    
    # Print conversion statistics
    if total_syscalls > 0:
        mapped_pct = ((total_syscalls - unmapped_count) / total_syscalls) * 100
        print(f"\n📊 Conversion Statistics:")
        print(f"   - Total syscalls processed: {total_syscalls:,}")
        print(f"   - Successfully mapped: {total_syscalls - unmapped_count:,} ({mapped_pct:.1f}%)")
        if unmapped_count > 0:
            print(f"   - Unmapped (kept as syscall_XXX): {unmapped_count:,}")
    
    return training_data

def download_adfa_ld(output_dir: Path) -> bool:
    """Download and convert ADFA-LD dataset"""
    print("\n" + "="*70)
    print("ADFA-LD Dataset Download")
    print("="*70)
    
    # ADFA-LD download URLs (these may need to be updated)
    # Note: Actual URLs may require registration or may have changed
    base_urls = [
        "https://www.unsw.adfa.edu.au/unsw-canberra-cyber/cybersecurity/ADFA-IDS-Datasets/",
        # Alternative sources may be available
    ]
    
    print("ℹ️  ADFA-LD Dataset Information:")
    print("   - Official site: https://www.unsw.adfa.edu.au/unsw-canberra-cyber/cybersecurity/ADFA-IDS-Datasets/")
    print("   - Format: Text files with one syscall per line")
    print("   - Contains: Normal sequences + Attack sequences")
    print("\n⚠️  Note: You may need to:")
    print("   1. Visit the official site to download")
    print("   2. Extract the archive manually")
    print("   3. Run this script with --adfa-dir pointing to extracted folder")
    
    return False  # Manual download required

def convert_dongting_format(dongting_dir: Path) -> List[Tuple[List[str], Dict]]:
    """
    Convert DongTing dataset format to our training data format
    
    DongTing dataset structure may vary - this is a template
    """
    training_data = []
    
    # This is a placeholder - actual format needs to be determined
    # when the dataset is downloaded
    print("⚠️  DongTing format converter - needs dataset structure analysis")
    
    return training_data

def download_dongting(output_dir: Path) -> bool:
    """Download and convert DongTing dataset"""
    print("\n" + "="*70)
    print("DongTing Dataset Download")
    print("="*70)
    
    # DongTing dataset from Zenodo
    zenodo_url = "https://zenodo.org/records/6627050"
    
    print(f"ℹ️  DongTing Dataset Information:")
    print(f"   - Zenodo: {zenodo_url}")
    print(f"   - Contains: 18,966 labeled normal and attack sequences")
    print(f"   - Covers: Linux kernels from past 5 years")
    print("\n⚠️  Note: You may need to:")
    print("   1. Visit Zenodo to download")
    print("   2. Extract the archive manually")
    print("   3. Run this script with --dongting-dir pointing to extracted folder")
    
    return False  # Manual download required

def save_training_data(training_data: List[Tuple[List[str], Dict]], 
                      output_file: Path, dataset_name: str) -> bool:
    """Save training data in our JSON format"""
    try:
        export_data = {
            'version': '1.0',
            'metadata': {
                'source': dataset_name,
                'total_samples': len(training_data),
                'feature_dimensions': 50,
                'format': 'syscall_sequences'
            },
            'samples': []
        }
        
        for syscalls, process_info in training_data:
            sample = {
                'syscalls': syscalls,
                'process_info': {
                    'cpu_percent': float(process_info.get('cpu_percent', 0.0)),
                    'memory_percent': float(process_info.get('memory_percent', 0.0)),
                    'num_threads': int(process_info.get('num_threads', 1)),
                    'pid': int(process_info.get('pid', 0)) if 'pid' in process_info else None
                }
            }
            if 'source' in process_info:
                sample['metadata'] = {'source': process_info['source'], 'label': process_info.get('label', 'normal')}
            export_data['samples'].append(sample)
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"✅ Saved {len(training_data)} samples to {output_file}")
        return True
    except Exception as e:
        print(f"❌ Error saving training data: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Download and convert real training datasets',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert ADFA-LD dataset (already downloaded)
  python3 scripts/download_real_datasets.py --adfa-dir /path/to/ADFA-LD --output datasets/adfa_ld_training.json
  
  # Convert DongTing dataset (already downloaded)
  python3 scripts/download_real_datasets.py --dongting-dir /path/to/DongTing --output datasets/dongting_training.json
  
  # Show download instructions
  python3 scripts/download_real_datasets.py --info
        """
    )
    
    parser.add_argument('--adfa-dir', type=str, help='Path to extracted ADFA-LD dataset directory')
    parser.add_argument('--dongting-dir', type=str, help='Path to extracted DongTing dataset directory')
    parser.add_argument('--output', type=str, default='datasets/real_training_data.json',
                       help='Output JSON file path (default: datasets/real_training_data.json)')
    parser.add_argument('--info', action='store_true', help='Show dataset information and download links')
    
    args = parser.parse_args()
    
    if args.info:
        print("\n" + "="*70)
        print("PUBLIC DATASETS FOR LINUX SYSCALL ANOMALY DETECTION")
        print("="*70)
        
        print("\n1. ADFA-LD (Australian Defence Force Academy Linux Dataset)")
        print("   URL: https://www.unsw.adfa.edu.au/unsw-canberra-cyber/cybersecurity/ADFA-IDS-Datasets/")
        print("   Format: Text files, one syscall per line")
        print("   Contains: Normal sequences + Attack sequences")
        print("   License: Academic use")
        
        print("\n2. DongTing Dataset")
        print("   URL: https://zenodo.org/records/6627050")
        print("   Size: 18,966 labeled sequences")
        print("   Coverage: Linux kernels from past 5 years")
        print("   License: Check Zenodo page")
        
        print("\n3. Other Potential Sources:")
        print("   - UNM datasets (University of New Mexico)")
        print("   - DARPA datasets (older, may have restrictions)")
        print("   - Academic research papers (check their supplementary materials)")
        
        print("\n" + "="*70)
        print("USAGE:")
        print("="*70)
        print("1. Download dataset from official source")
        print("2. Extract archive to a directory")
        print("3. Run: python3 scripts/download_real_datasets.py --adfa-dir /path/to/extracted --output datasets/adfa_training.json")
        print("4. Train models: python3 scripts/train_with_dataset.py --file datasets/adfa_training.json")
        return 0
    
    # Create output directory
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    training_data = []
    
    # Process ADFA-LD
    if args.adfa_dir:
        adfa_dir = Path(args.adfa_dir)
        if not adfa_dir.exists():
            print(f"❌ ADFA-LD directory not found: {adfa_dir}")
            return 1
        
        print("\n📂 Converting ADFA-LD dataset...")
        adfa_data = convert_adfa_ld_format(adfa_dir)
        training_data.extend(adfa_data)
        print(f"✅ Converted {len(adfa_data)} samples from ADFA-LD")
    
    # Process DongTing
    if args.dongting_dir:
        dongting_dir = Path(args.dongting_dir)
        if not dongting_dir.exists():
            print(f"❌ DongTing directory not found: {dongting_dir}")
            return 1
        
        print("\n📂 Converting DongTing dataset...")
        dongting_data = convert_dongting_format(dongting_dir)
        training_data.extend(dongting_data)
        print(f"✅ Converted {len(dongting_data)} samples from DongTing")
    
    if not training_data:
        print("\n❌ No training data converted. Use --info to see download instructions.")
        print("   Or provide --adfa-dir or --dongting-dir with extracted dataset directories.")
        return 1
    
    # Save converted data
    dataset_name = "real_dataset"
    if args.adfa_dir:
        dataset_name = "ADFA-LD"
    elif args.dongting_dir:
        dataset_name = "DongTing"
    
    if save_training_data(training_data, output_file, dataset_name):
        print(f"\n✅ Successfully converted and saved {len(training_data)} samples")
        print(f"📁 Output file: {output_file}")
        print(f"\n📝 Next steps:")
        print(f"   1. Review the data: cat {output_file} | head -50")
        print(f"   2. Train models: python3 scripts/train_with_dataset.py --file {output_file}")
        print(f"   3. Or combine with existing: python3 scripts/train_with_dataset.py --file {output_file} --append")
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())

