
checker.raw:     file format binary


Disassembly of section .data:

000000000000739a <.data>:
    739a:	f3 0f 1e fa          	endbr64
    739e:	53                   	push   rbx
    739f:	55                   	push   rbp
    73a0:	41 54                	push   r12
    73a2:	48 89 e5             	mov    rbp,rsp
    73a5:	48 8d 1d ea ff ff ff 	lea    rbx,[rip+0xffffffffffffffea]        # 0x7396
    73ac:	48 8d 05 01 00 00 00 	lea    rax,[rip+0x1]        # 0x73b4
    73b3:	48 25 00 f0 ff ff    	and    rax,0xfffffffffffff000
    73b9:	48 05 60 3d 00 00    	add    rax,0x3d60
    73bf:	48 8b 00             	mov    rax,QWORD PTR [rax]
    73c2:	48 85 c0             	test   rax,rax
    73c5:	0f 84 87 02 00 00    	je     0x7652
    73cb:	48 8b 48 10          	mov    rcx,QWORD PTR [rax+0x10]
    73cf:	48 85 c9             	test   rcx,rcx
    73d2:	0f 84 7a 02 00 00    	je     0x7652
    73d8:	80 39 cc             	cmp    BYTE PTR [rcx],0xcc
    73db:	0f 84 71 02 00 00    	je     0x7652
    73e1:	b8 02 00 00 00       	mov    eax,0x2
    73e6:	48 8d 3d 71 02 00 00 	lea    rdi,[rip+0x271]        # 0x765e
    73ed:	31 f6                	xor    esi,esi
    73ef:	31 d2                	xor    edx,edx
    73f1:	0f 05                	syscall
    73f3:	85 c0                	test   eax,eax
    73f5:	78 70                	js     0x7467
    73f7:	48 81 ec 00 02 00 00 	sub    rsp,0x200
    73fe:	89 c7                	mov    edi,eax
    7400:	31 c0                	xor    eax,eax
    7402:	48 89 e6             	mov    rsi,rsp
    7405:	ba 00 02 00 00       	mov    edx,0x200
    740a:	0f 05                	syscall
    740c:	41 89 c0             	mov    r8d,eax
    740f:	45 85 c0             	test   r8d,r8d
    7412:	7e 53                	jle    0x7467
    7414:	49 89 e4             	mov    r12,rsp
    7417:	4f 8d 0c 04          	lea    r9,[r12+r8*1]
    741b:	49 83 e9 0c          	sub    r9,0xc
    741f:	4d 39 cc             	cmp    r12,r9
    7422:	77 43                	ja     0x7467
    7424:	49 8b 04 24          	mov    rax,QWORD PTR [r12]
    7428:	48 3b 05 47 02 00 00 	cmp    rax,QWORD PTR [rip+0x247]        # 0x7676
    742f:	75 31                	jne    0x7462
    7431:	41 0f b7 44 24 08    	movzx  eax,WORD PTR [r12+0x8]
    7437:	66 3b 05 40 02 00 00 	cmp    ax,WORD PTR [rip+0x240]        # 0x767e
    743e:	75 22                	jne    0x7462
    7440:	49 83 c4 0a          	add    r12,0xa
    7444:	41 0f b6 04 24       	movzx  eax,BYTE PTR [r12]
    7449:	3c 20                	cmp    al,0x20
    744b:	74 06                	je     0x7453
    744d:	3c 09                	cmp    al,0x9
    744f:	74 02                	je     0x7453
    7451:	eb 05                	jmp    0x7458
    7453:	49 ff c4             	inc    r12
    7456:	eb ec                	jmp    0x7444
    7458:	3c 30                	cmp    al,0x30
    745a:	0f 85 f2 01 00 00    	jne    0x7652
    7460:	eb 05                	jmp    0x7467
    7462:	49 ff c4             	inc    r12
    7465:	eb b8                	jmp    0x741f
    7467:	48 8d 05 01 00 00 00 	lea    rax,[rip+0x1]        # 0x746f
    746e:	48 25 00 f0 ff ff    	and    rax,0xfffffffffffff000
    7474:	48 05 60 3d 00 00    	add    rax,0x3d60
    747a:	48 8b 00             	mov    rax,QWORD PTR [rax]
    747d:	48 85 c0             	test   rax,rax
    7480:	0f 84 cc 01 00 00    	je     0x7652
    7486:	48 8b 50 08          	mov    rdx,QWORD PTR [rax+0x8]
    748a:	31 c9                	xor    ecx,ecx
    748c:	48 85 d2             	test   rdx,rdx
    748f:	74 11                	je     0x74a2
    7491:	ff c1                	inc    ecx
    7493:	83 f9 07             	cmp    ecx,0x7
    7496:	0f 87 b6 01 00 00    	ja     0x7652
    749c:	48 8b 52 18          	mov    rdx,QWORD PTR [rdx+0x18]
    74a0:	eb ea                	jmp    0x748c
    74a2:	48 8d bb 2a 3e 00 00 	lea    rdi,[rbx+0x3e2a]
    74a9:	80 3f 00             	cmp    BYTE PTR [rdi],0x0
    74ac:	0f 84 a0 01 00 00    	je     0x7652
    74b2:	81 3f 66 6c 61 67    	cmp    DWORD PTR [rdi],0x67616c66
    74b8:	0f 85 94 01 00 00    	jne    0x7652
    74be:	80 7f 04 7b          	cmp    BYTE PTR [rdi+0x4],0x7b
    74c2:	0f 85 8a 01 00 00    	jne    0x7652
    74c8:	80 7f 25 7d          	cmp    BYTE PTR [rdi+0x25],0x7d
    74cc:	0f 85 80 01 00 00    	jne    0x7652
    74d2:	80 7f 26 00          	cmp    BYTE PTR [rdi+0x26],0x0
    74d6:	0f 85 76 01 00 00    	jne    0x7652
    74dc:	48 81 ec 20 01 00 00 	sub    rsp,0x120
    74e3:	31 c9                	xor    ecx,ecx
    74e5:	0f b6 44 4f 05       	movzx  eax,BYTE PTR [rdi+rcx*2+0x5]
    74ea:	0f b6 54 4f 06       	movzx  edx,BYTE PTR [rdi+rcx*2+0x6]
    74ef:	83 c8 20             	or     eax,0x20
    74f2:	83 ca 20             	or     edx,0x20
    74f5:	44 8d 40 d0          	lea    r8d,[rax-0x30]
    74f9:	41 83 f8 09          	cmp    r8d,0x9
    74fd:	76 0e                	jbe    0x750d
    74ff:	44 8d 40 a9          	lea    r8d,[rax-0x57]
    7503:	41 83 f8 0f          	cmp    r8d,0xf
    7507:	0f 87 45 01 00 00    	ja     0x7652
    750d:	44 8d 4a d0          	lea    r9d,[rdx-0x30]
    7511:	41 83 f9 09          	cmp    r9d,0x9
    7515:	76 0e                	jbe    0x7525
    7517:	44 8d 4a a9          	lea    r9d,[rdx-0x57]
    751b:	41 83 f9 0f          	cmp    r9d,0xf
    751f:	0f 87 2d 01 00 00    	ja     0x7652
    7525:	41 c1 e0 04          	shl    r8d,0x4
    7529:	45 09 c8             	or     r8d,r9d
    752c:	44 88 04 0c          	mov    BYTE PTR [rsp+rcx*1],r8b
    7530:	ff c1                	inc    ecx
    7532:	83 f9 10             	cmp    ecx,0x10
    7535:	75 ae                	jne    0x74e5
    7537:	48 8b 05 48 01 00 00 	mov    rax,QWORD PTR [rip+0x148]        # 0x7686
    753e:	48 33 05 49 01 00 00 	xor    rax,QWORD PTR [rip+0x149]        # 0x768e
    7545:	48 89 44 24 10       	mov    QWORD PTR [rsp+0x10],rax
    754a:	48 8b 15 45 01 00 00 	mov    rdx,QWORD PTR [rip+0x145]        # 0x7696
    7551:	48 33 15 46 01 00 00 	xor    rdx,QWORD PTR [rip+0x146]        # 0x769e
    7558:	48 89 54 24 18       	mov    QWORD PTR [rsp+0x18],rdx
    755d:	4c 8b 04 24          	mov    r8,QWORD PTR [rsp]
    7561:	49 31 c0             	xor    r8,rax
    7564:	4c 8b 4c 24 08       	mov    r9,QWORD PTR [rsp+0x8]
    7569:	49 31 d1             	xor    r9,rdx
    756c:	b9 02 00 00 00       	mov    ecx,0x2
    7571:	49 bc 15 7c 4a 7f b9 	movabs r12,0x9e3779b97f4a7c15
    7578:	79 37 9e 
    757b:	4f 8d 1c 24          	lea    r11,[r12+r12*1]
    757f:	48 8b 44 cc 08       	mov    rax,QWORD PTR [rsp+rcx*8+0x8]
    7584:	48 8b 14 cc          	mov    rdx,QWORD PTR [rsp+rcx*8]
    7588:	49 89 c2             	mov    r10,rax
    758b:	49 09 d2             	or     r10,rdx
    758e:	48 89 c6             	mov    rsi,rax
    7591:	48 21 d6             	and    rsi,rdx
    7594:	49 01 f2             	add    r10,rsi
    7597:	49 c1 c2 0d          	rol    r10,0xd
    759b:	48 c1 ca 07          	ror    rdx,0x7
    759f:	4c 89 d6             	mov    rsi,r10
    75a2:	48 09 d6             	or     rsi,rdx
    75a5:	4c 89 d7             	mov    rdi,r10
    75a8:	48 21 d7             	and    rdi,rdx
    75ab:	48 29 fe             	sub    rsi,rdi
    75ae:	49 89 f2             	mov    r10,rsi
    75b1:	4d 31 da             	xor    r10,r11
    75b4:	4c 89 54 cc 10       	mov    QWORD PTR [rsp+rcx*8+0x10],r10
    75b9:	4d 01 e3             	add    r11,r12
    75bc:	ff c1                	inc    ecx
    75be:	83 f9 20             	cmp    ecx,0x20
    75c1:	75 bc                	jne    0x757f
    75c3:	b9 02 00 00 00       	mov    ecx,0x2
    75c8:	4c 89 c8             	mov    rax,r9
    75cb:	48 8b 54 cc 10       	mov    rdx,QWORD PTR [rsp+rcx*8+0x10]
    75d0:	49 89 c2             	mov    r10,rax
    75d3:	49 09 d2             	or     r10,rdx
    75d6:	48 89 c6             	mov    rsi,rax
    75d9:	48 21 d6             	and    rsi,rdx
    75dc:	49 01 f2             	add    r10,rsi
    75df:	49 c1 c2 0d          	rol    r10,0xd
    75e3:	48 89 c6             	mov    rsi,rax
    75e6:	48 c1 c6 1d          	rol    rsi,0x1d
    75ea:	4c 89 d7             	mov    rdi,r10
    75ed:	48 09 f7             	or     rdi,rsi
    75f0:	4c 89 d2             	mov    rdx,r10
    75f3:	48 21 f2             	and    rdx,rsi
    75f6:	48 29 d7             	sub    rdi,rdx
    75f9:	49 89 fa             	mov    r10,rdi
    75fc:	48 89 c6             	mov    rsi,rax
    75ff:	48 c1 c6 2f          	rol    rsi,0x2f
    7603:	4c 89 d7             	mov    rdi,r10
    7606:	48 09 f7             	or     rdi,rsi
    7609:	4c 89 d2             	mov    rdx,r10
    760c:	48 21 f2             	and    rdx,rsi
    760f:	48 01 d7             	add    rdi,rdx
    7612:	49 89 fa             	mov    r10,rdi
    7615:	4c 89 c0             	mov    rax,r8
    7618:	4c 31 d0             	xor    rax,r10
    761b:	4d 89 c8             	mov    r8,r9
    761e:	49 89 c1             	mov    r9,rax
    7621:	ff c1                	inc    ecx
    7623:	83 f9 20             	cmp    ecx,0x20
    7626:	75 a0                	jne    0x75c8
    7628:	48 8d 3d 77 00 00 00 	lea    rdi,[rip+0x77]        # 0x76a6
    762f:	4c 3b 07             	cmp    r8,QWORD PTR [rdi]
    7632:	75 1e                	jne    0x7652
    7634:	4c 3b 4f 08          	cmp    r9,QWORD PTR [rdi+0x8]
    7638:	75 18                	jne    0x7652
    763a:	b8 01 00 00 00       	mov    eax,0x1
    763f:	bf 01 00 00 00       	mov    edi,0x1
    7644:	48 8d 35 6b 00 00 00 	lea    rsi,[rip+0x6b]        # 0x76b6
    764b:	ba 0e 00 00 00       	mov    edx,0xe
    7650:	0f 05                	syscall
    7652:	48 89 ec             	mov    rsp,rbp
    7655:	41 5c                	pop    r12
    7657:	5d                   	pop    rbp
    7658:	5b                   	pop    rbx
    7659:	c3                   	ret
    765a:	0f 1f 40 00          	nop    DWORD PTR [rax+0x0]
    765e:	2f                   	(bad)
    765f:	70 72                	jo     0x76d3
    7661:	6f                   	outs   dx,DWORD PTR [rsi]
    7662:	63 2f                	movsxd ebp,DWORD PTR [rdi]
    7664:	73 65                	jae    0x76cb
    7666:	6c                   	ins    BYTE PTR [rdi],dx
    7667:	66 2f                	data16 (bad)
    7669:	73 74                	jae    0x76df
    766b:	61                   	(bad)
    766c:	74 75                	je     0x76e3
    766e:	73 00                	jae    0x7670
    7670:	90                   	nop
    7671:	0f 1f 44 00 00       	nop    DWORD PTR [rax+rax*1+0x0]
    7676:	54                   	push   rsp
    7677:	72 61                	jb     0x76da
    7679:	63 65 72             	movsxd esp,DWORD PTR [rbp+0x72]
    767c:	50                   	push   rax
    767d:	69 64 3a 90 0f 1f 44 	imul   esp,DWORD PTR [rdx+rdi*1-0x70],0x441f0f
    7684:	00 
    7685:	00 95 27 bb 17 79    	add    BYTE PTR [rbp+0x7917bb27],dl
    768b:	18 68 d8             	sbb    BYTE PTR [rax-0x28],ch
    768e:	13 92 f4 35 9e a6    	adc    edx,DWORD PTR [rdx-0x5961ca0c]
    7694:	ce                   	(bad)
    7695:	c7                   	(bad)
    7696:	eb b6                	jmp    0x764e
    7698:	68 9d 8e c7 9e       	push   0xffffffff9ec78e9d
    769d:	93                   	xchg   ebx,eax
    769e:	b3 1b                	mov    bl,0x1b
    76a0:	33 52 18             	xor    edx,DWORD PTR [rdx+0x18]
    76a3:	92                   	xchg   edx,eax
    76a4:	62 c5 d7 d2 a7       	(bad)
    76a9:	4f a8 35             	rex.WRXB test al,0x35
    76ac:	b3 4f                	mov    bl,0x4f
    76ae:	9f                   	lahf
    76af:	f4                   	hlt
    76b0:	f4                   	hlt
    76b1:	b4 e3                	mov    ah,0xe3
    76b3:	83 a1 02 66 6c 61 67 	and    DWORD PTR [rcx+0x616c6602],0x67
    76ba:	20 61 63             	and    BYTE PTR [rcx+0x63],ah
    76bd:	63 65 70             	movsxd esp,DWORD PTR [rbp+0x70]
    76c0:	74 65                	je     0x7727
    76c2:	64                   	fs
    76c3:	0a                   	.byte 0xa
    76c4:	90                   	nop
    76c5:	90                   	nop
