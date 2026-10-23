"""生成最小的 Win7 兼容 api-ms-win-core-path-l1-1-0.dll 转发层。

原理：
  PE 转发层 DLL 的导出表每一项不是指向真实代码，而是指向一个形如
  "KernelBase.PathCchCanonicalize" 的字符串（RVA 在 0x80000000 以内且含 '.'）。
  PE 加载器看到这种 entry，就把调用转发给指定 DLL 的指定函数。

  这个 DLL 的所有函数在 Win7 上都是 KernelBase.dll 的真实导出，
  所以只要导出表写对，Win7 就能正常加载。

用法：python _gen_path_dll.py
"""
import struct, os, time

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "win7_hacks", "api-ms-win-core-path-l1-1-0.dll")

# 从 MinGW-w64 的 .def 文件来的 22 个导出函数
EXPORTS = [
    "PathAllocCanonicalize",
    "PathAllocCombine",
    "PathCchAddBackslash",
    "PathCchAddBackslashEx",
    "PathCchAddExtension",
    "PathCchAppend",
    "PathCchAppendEx",
    "PathCchCanonicalize",
    "PathCchCanonicalizeEx",
    "PathCchCombine",
    "PathCchCombineEx",
    "PathCchFindExtension",
    "PathCchIsRoot",
    "PathCchRemoveBackslash",
    "PathCchRemoveBackslashEx",
    "PathCchRemoveExtension",
    "PathCchRemoveFileSpec",
    "PathCchRenameExtension",
    "PathCchSkipRoot",
    "PathCchStripPrefix",
    "PathCchStripToRoot",
    "PathIsUNCEx",
]

# 64-bit PE (PE32+)
MACHINE = 0x8664
IMAGE_FILE_MACHINE_AMD64 = MACHINE
IMAGE_FILE_EXECUTABLE_IMAGE = 0x0002
IMAGE_FILE_LARGE_ADDRESS_AWARE = 0x0020
IMAGE_FILE_DLL = 0x2000
IMAGE_DLL_CHARACTERISTICS_DYNAMIC_BASE      = 0x0040
IMAGE_DLL_CHARACTERISTICS_NX_COMPAT         = 0x0100
IMAGE_SUBSYSTEM_WINDOWS_GUI                 = 2
IMAGE_BASE_AMD64                            = 0x0000000180000000

# ---- 构造 DOS Header + DOS Stub ----
# DOS Header (64 bytes)
dos_header = bytearray(b"MZ")
dos_header += b"\x90" * 58  # padding
# PE 签名在 e_lfanew 偏移 0x3C
dos_header[0x3C:0x40] = struct.pack("<I", 0x80)  # e_lfanew = 128

# DOS stub (简洁版：只输出 This program cannot run in DOS mode)
dos_stub = (
    b"\x0e\x1f\xba\x0e\x00\xb4\x09\xcd\x21\xb8\x01\x4c\xcd\x21"
    b"This program cannot be run in DOS mode.\r\r\n$\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
)
dos_header = bytes(dos_header) + dos_stub
# 填充到 128 字节（e_lfanew 指向的位置）
dos_header = dos_header.ljust(0x80, b"\x00")

# ---- PE Signature + COFF Header + Optional Header ----
pe_sig = b"PE\x00\x00"

# COFF Header (20 bytes)
coff = struct.pack("<HHIIIHH",
    IMAGE_FILE_MACHINE_AMD64,
    2,          # NumberOfSections (空的 .text + .rdata)
    0,          # TimeDateStamp
    0,          # PointerToSymbolTable
    0,          # NumberOfSymbols
    0xF0,       # SizeOfOptionalHeader (PE32+ standard + data dirs)
    IMAGE_FILE_EXECUTABLE_IMAGE | IMAGE_FILE_LARGE_ADDRESS_AWARE | IMAGE_FILE_DLL,
)

# Optional Header Standard Fields (28 bytes)
opt_std = struct.pack("<HBBIIIIIII",
    0x020b,      # Magic: PE32+
    1,           # MajorLinkerVersion
    0,           # MinorLinkerVersion
    0,           # SizeOfCode (空)
    0,           # SizeOfInitializedData
    0,           # SizeOfUninitializedData
    0x1000,      # AddressOfEntryPoint (指向 .rdata 起始)
    0x1000,      # BaseOfCode (PE32+)
)

# Optional Header Windows-specific Fields (PE32+: 88 bytes vs PE32's 68)
opt_win = struct.pack("<QQIIIIHHIIIIII",
    IMAGE_BASE_AMD64,
    0x1000,      # SectionAlignment
    0x1000,      # FileAlignment
    6, 0,        # MajorOS / MinorOS
    0, 0,        # MajorImage / MinorImage
    6, 0,        # MajorSubsystem / MinorSubsystem
    0,           # Win32VersionValue
    0x2000,      # SizeOfImage (ImageBase + SizeOfImage = 18002000)
    0x1000,      # SizeOfHeaders
    0,           # CheckSum
    IMAGE_SUBSYSTEM_WINDOWS_GUI,
    IMAGE_DLL_CHARACTERISTICS_DYNAMIC_BASE | IMAGE_DLL_CHARACTERISTICS_NX_COMPAT,
    0x100000,    # SizeOfStackReserve
    0x1000,      # SizeOfStackCommit
    0x100000,    # SizeOfHeapReserve
    0x1000,      # SizeOfHeapCommit
    0,           # LoaderFlags
    16,          # NumberOfRvaAndSizes
)

# Data Directories (16 entries, 128 bytes)
# 只填 Export Directory，其他全零
export_dd_rva = 0x1000      # .rdata 起始
export_dd_size = 40 + 22*12 + (22+1)*4 + (1+22)*4  # 估算
data_dirs = bytearray(16 * 8)
struct.pack_into("<II", data_dirs, 0*8, export_dd_rva, export_dd_size)  # Export

# 现在先把所有字符串收集好，再算准确的导出表大小
forwarder_base = 0x1000 + 128 + 40   # 假设 Export Directory Header 40 bytes + Names Table 4 bytes + Functions Table + Names Ordinal Base

# 先写节表（算好偏移后会回填），然后 .rdata 内容
# .text 节（空）
# .rdata 节（导出表 + 字符串）

# ---- 构造 .rdata ----
rdata = bytearray()

# 1) Export Directory Header (40 bytes)
# struct _IMAGE_EXPORT_DIRECTORY {
#   DWORD Characteristics;
#   DWORD TimeDateStamp;
#   WORD  MajorVersion;
#   WORD  MinorVersion;
#   PCHAR Name;
#   DWORD Base;
#   DWORD NumberOfFunctions;
#   DWORD NumberOfNames;
#   PDWORD AddressOfFunctions;     // RVA from base of image
#   PDWORD AddressOfNames;         // RVA from base of image
#   PWORD  AddressOfNameOrdinals;  // RVA from base of image
# }
export_dir_rva = 0x1000
name_rva = 0x1000 + 40 + (22+1)*4 + 22*4 + 22*2
functions_rva = 0x1000 + 40
names_rva = 0x1000 + 40 + (22+1)*4
ordinals_rva = 0x1000 + 40 + (22+1)*4 + 22*4

export_hdr = struct.pack("<IIHHiIIIIII",
    0,             # Characteristics
    int(time.time()),  # TimeDateStamp
    0, 0,          # MajorVersion / MinorVersion
    name_rva,      # Name (DLL 名字)
    1,             # Base (ordinal base)
    len(EXPORTS),  # NumberOfFunctions
    len(EXPORTS),  # NumberOfNames
    functions_rva, # AddressOfFunctions
    names_rva,     # AddressOfNames
    ordinals_rva,  # AddressOfNameOrdinals
)
rdata += export_hdr

# 2) AddressOfFunctions: 每个函数的 RVA（指向 forwarder 字符串）
#    先写占位，等知道每个 forwarder 的 RVA 后回填
functions_pos = len(rdata)
rdata += b"\x00" * (len(EXPORTS) * 4)

# 3) AddressOfNames: 每个名字字符串的 RVA
names_pos = len(rdata)
rdata += b"\x00" * ((len(EXPORTS) + 1) * 4)  # +1 是 DLL 名字

# 4) AddressOfNameOrdinals: 每个名字对应的 ordinal（从 0 开始）
ordinals_pos = len(rdata)
rdata += b"\x00" * (len(EXPORTS) * 2)

# 5) DLL 名字
dll_name_pos = len(rdata)
dll_name = b"api-ms-win-core-path-l1-1-0.dll\x00"
rdata += dll_name

# 6) 每个导出函数的名字字符串 + 对应的 forwarder 字符串
name_rvas = []
forwarder_rvas = []

for func in EXPORTS:
    name_rvas.append(len(rdata))
    rdata += func.encode() + b"\x00"
    fw = f"KernelBase.{func}".encode() + b"\x00"
    forwarder_rvas.append(len(rdata))
    rdata += fw

# 7) 回填 AddressOfFunctions（指向 forwarder 字符串的 RVA）
for i, fw_rva in enumerate(forwarder_rvas):
    struct.pack_into("<I", rdata, functions_pos + i*4,
                     fw_rva + export_dir_rva)

# 8) 回填 AddressOfNames（指向函数名字字符串的 RVA）
struct.pack_into("<I", rdata, names_pos, dll_name_pos + export_dir_rva)
for i, n_rva in enumerate(name_rvas):
    struct.pack_into("<I", rdata, names_pos + 4 + i*4, n_rva + export_dir_rva)

# 9) 回填 AddressOfNameOrdinals（ordinal index = i，因为函数是顺序排列的）
for i in range(len(EXPORTS)):
    struct.pack_into("<H", rdata, ordinals_pos + i*2, i)

# 对齐 .rdata 到 0x1000
rdata_size_raw = len(rdata)
rdata_size_file = ((rdata_size_raw + 0xFFF) // 0x1000) * 0x1000
rdata += b"\x00" * (rdata_size_file - rdata_size_raw)

# 现在重新算一遍所有 RVA（.rdata 从 0x1000 开始）
export_dir_rva = 0x1000
name_rva = 0x1000 + dll_name_pos
functions_rva = 0x1000 + functions_pos
names_rva = 0x1000 + names_pos
ordinals_rva = 0x1000 + ordinals_pos

# 重写 Export Directory Header（RVA 都换成真实的 ImageBase + RVA 范围内）
export_hdr = struct.pack("<IIHHiIIIIII",
    0,
    int(time.time()),
    0, 0,
    name_rva,
    1,
    len(EXPORTS),
    len(EXPORTS),
    functions_rva,
    names_rva,
    ordinals_rva,
)

# 重写 .rdata 内容（这次所有 RVA 都是绝对的）
rdata2 = bytearray()
rdata2 += export_hdr
# functions RVAs -> forwarder RVAs
for fw_rva in forwarder_rvas:
    rdata2 += struct.pack("<I", 0x1000 + fw_rva)  # forwarder 的绝对 RVA
# names RVAs
rdata2 += struct.pack("<I", 0x1000 + dll_name_pos)
for n_rva in name_rvas:
    rdata2 += struct.pack("<I", 0x1000 + n_rva)
# ordinals
for i in range(len(EXPORTS)):
    rdata2 += struct.pack("<H", i)
# DLL name
rdata2 += dll_name
# 函数名 + forwarder
for i, func in enumerate(EXPORTS):
    rdata2 += func.encode() + b"\x00"
    rdata2 += f"KernelBase.{func}".encode() + b"\x00"

# 对齐
rdata2_size_raw = len(rdata2)
rdata2_aligned = ((rdata2_size_raw + 0xFFF) // 0x1000) * 0x1000
rdata2 += b"\x00" * (rdata2_aligned - rdata2_size_raw)
assert len(rdata2) == rdata_size_file, f"{len(rdata2)} != {rdata_size_file}"

# 现在算节区表位置 + 整个 PE 的 header 大小（需要先确定 NumberOfSections 和 SizeOfImage）
size_of_headers = 0x1000  # 固定，PE 加载器会按 FileAlignment 对齐
text_size_file  = 0x1000  # 空的 .text，但节必须存在
text_rva = 0x1000
text_raw = 0x1000

rdata_rva = 0x2000
rdata_raw = 0x2000

# 构造两个节的 IMAGE_SECTION_HEADER（每个 40 bytes）
section_text = struct.pack("<8sIIIIIIHHI",
    b".text\x00\x00\x00",   # Name
    0,                       # VirtualSize
    text_rva,                # VirtualAddress
    0,                       # SizeOfRawData
    text_raw,                # PointerToRawData
    0, 0,                    # PointerToRelocations / PointerToLinenumbers
    0, 0,                    # NumberOfRelocations / NumberOfLinenumbers
    0x60000060,              # Characteristics: CODE | EXECUTE_READ
)
section_rdata = struct.pack("<8sIIIIIIHHI",
    b".rdata\x00\x00",      # Name
    len(rdata2),             # VirtualSize (raw aligned to 0x1000)
    rdata_rva,               # VirtualAddress
    len(rdata2),             # SizeOfRawData
    rdata_raw,               # PointerToRawData
    0, 0,
    0, 0,
    0x40000040,              # Characteristics: INITIALIZED_DATA | READ
)

# 拼 PE Header 块
pe_header = (
    dos_header +
    pe_sig +
    coff +
    opt_std + opt_win +
    bytes(data_dirs) +
    section_text +
    section_rdata
)

# 填充到 SizeOfHeaders
pe_header = pe_header.ljust(size_of_headers, b"\x00")

# 更新 COFF Header 的 NumberOfSections
pe_header = bytearray(pe_header)
struct.pack_into("<H", pe_header, 0x84, 2)  # NumberOfSections offset
# 更新 Optional Header 的 SizeOfImage
struct.pack_into("<I", pe_header, 0x84 + 4 + 2 + 2 + 4 + 4 + 2 + 2 + 2 + 2 + 4 + 4 + 4 + 2 + 2 + 2 + 4,  # 手动数的偏移
                 0x3000)  # .text(4KB) + .rdata(4KB) = 8KB = 0x2000... 等等
# 重新算 SizeOfImage
# .text 从 0x1000 开始，大小 0x1000
# .rdata 从 0x2000 开始，大小 0x1000
# SizeOfImage = 0x3000
size_of_image = 0x3000
# 重新定位 size_of_image 在 optional header 里的偏移
# Optional Header PE32+ 里：Windows fields 从 magic(2) + linker(4) + sizes(4+4+4) + entry(4) + base(4) = 2+4+12+4+4 = 26 字节后开始
# 然后 Windows-specific 里 SizeOfImage 在第 11 个字段（QQIIIIHHIIIIII 里的第 11 个 I）
# base at 0x80(DOS) + 4(sig) + 20(coff) + 28(opt_std) + 4 = 0x110 后的 88 bytes = 0x110 + 88
# SizeOfImage 在 11th field of <QQIIIIHHIIIIII => offset 10*4 = 40 bytes into win fields
# 所以 opt_win + 40 = 0x110 + 28 + 40 = 0x140 — 不对，让我数清楚
# Actually just write the opt_win bytes directly with correct SizeOfImage
opt_win = struct.pack("<QQIIIIHHIIIIII",
    IMAGE_BASE_AMD64,
    0x1000, 0x1000,
    6, 0, 0, 0, 0, 0,  # MajorOS/MinorOS/ImgSubsys
    IMAGE_SUBSYSTEM_WINDOWS_GUI,
    IMAGE_DLL_CHARACTERISTICS_DYNAMIC_BASE | IMAGE_DLL_CHARACTERISTICS_NX_COMPAT,
    0x100000, 0x1000, 0x100000, 0x1000, 0,
    size_of_image, 0x1000, 0, 16,
)
pe_header = (
    dos_header +
    pe_sig +
    coff +
    opt_std + opt_win +
    bytes(data_dirs) +
    section_text + section_rdata
)
pe_header = pe_header.ljust(size_of_headers, b"\x00")

# 导出表数据目录里的 SizeOfExportDirectory 需要改
export_dir_size = 40 + (len(EXPORTS)+1)*4 + len(EXPORTS)*4 + len(EXPORTS)*2 + len(dll_name) + sum(len(f)+1 for f in EXPORTS) + sum(len("KernelBase."+f)+1 for f in EXPORTS)
# 40(ExportHeader) + functions_RVA + names_RVA + ordinals + dll_name + func_names + forwarders
export_dir_size = (
    40 +
    len(EXPORTS) * 4 +                     # AddressOfFunctions
    (len(EXPORTS) + 1) * 4 +               # AddressOfNames (dll name + func names)
    len(EXPORTS) * 2 +                     # AddressOfNameOrdinals
    len(dll_name) +
    sum(len(f)+1 for f in EXPORTS) +
    sum(len("KernelBase."+f)+1 for f in EXPORTS)
)
# 重写 Export Data Directory 的 Size
struct.pack_into("<I", pe_header, 0x98, export_dir_size)

# .text 节（空）
text_block = b"\x00" * 0x1000

# 拼最终 DLL
dll = pe_header + text_block + rdata2

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "wb") as f:
    f.write(dll)

import hashlib
h = hashlib.sha256(dll).hexdigest().upper()
print(f"生成 {OUT}")
print(f"大小 {len(dll)} bytes, SHA256 {h}")

# 用 pefile 验证一下
import pefile
pe = pefile.PE(data=dll)
print(f"\nPE 验证:")
print(f"  Machine: {hex(pe.FILE_HEADER.Machine)}")
print(f"  Subsystem: {pe.OPTIONAL_HEADER.Subsystem}")
print(f"  Sections: {[s.Name.decode().rstrip('\x00') for s in pe.sections]}")
if hasattr(pe, "DIRECTORY_ENTRY_EXPORT"):
    names = []
    for e in pe.DIRECTORY_ENTRY_EXPORT.symbols:
        nm = e.name.decode() if e.name else f"ordinal{e.ordinal}"
        names.append(nm)
    print(f"  导出 {len(names)} 个: {', '.join(names[:4])}...")
print("OK - forwarder DLL 生成成功")
