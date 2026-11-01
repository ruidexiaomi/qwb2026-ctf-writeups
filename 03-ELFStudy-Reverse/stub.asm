
stub.raw:     file format binary


Disassembly of section .data:

0000000000007325 <.data>:
    7325:	53                   	push   rbx
    7326:	48 8d 1d f8 ff ff ff 	lea    rbx,[rip+0xfffffffffffffff8]        # 0x7325
    732d:	48 8d 05 01 00 00 00 	lea    rax,[rip+0x1]        # 0x7335
    7334:	48 25 00 f0 ff ff    	and    rax,0xfffffffffffff000
    733a:	48 05 60 3d 00 00    	add    rax,0x3d60
    7340:	48 8b 00             	mov    rax,QWORD PTR [rax]
    7343:	48 85 c0             	test   rax,rax
    7346:	74 3b                	je     0x7383
    7348:	48 8b 48 10          	mov    rcx,QWORD PTR [rax+0x10]
    734c:	48 85 c9             	test   rcx,rcx
    734f:	74 32                	je     0x7383
    7351:	80 39 cc             	cmp    BYTE PTR [rcx],0xcc
    7354:	74 2d                	je     0x7383
    7356:	48 8d bb 71 00 00 00 	lea    rdi,[rbx+0x71]
    735d:	b9 cb 00 00 00       	mov    ecx,0xcb
    7362:	31 c0                	xor    eax,eax
    7364:	31 04 8f             	xor    DWORD PTR [rdi+rcx*4],eax
    7367:	74 1a                	je     0x7383
    7369:	03 04 8f             	add    eax,DWORD PTR [rdi+rcx*4]
    736c:	e2 f6                	loop   0x7364
    736e:	48 8d 83 0f c8 ff ff 	lea    rax,[rbx-0x37f1]
    7375:	c6 00 e8             	mov    BYTE PTR [rax],0xe8
    7378:	c7 40 01 61 38 00 00 	mov    DWORD PTR [rax+0x1],0x3861
    737f:	c6 40 05 c3          	mov    BYTE PTR [rax+0x5],0xc3
    7383:	53                   	push   rbx
    7384:	5f                   	pop    rdi
    7385:	6a 61                	push   0x61
    7387:	59                   	pop    rcx
    7388:	31 c0                	xor    eax,eax
    738a:	5b                   	pop    rbx
    738b:	f3 aa                	rep stos BYTE PTR [rdi],al
    738d:	c3                   	ret
    738e:	00 00                	add    BYTE PTR [rax],al
    7390:	00 00                	add    BYTE PTR [rax],al
    7392:	00 00                	add    BYTE PTR [rax],al
	...
