****************************************
* CoCoIDE 6809 disassembly (best-effort)
* Aimed at lwasm: labels + indented ops
* Data-as-code may still need hand cleanup
****************************************

	org	$6200
* segment load=$6200 len=837
L6200
	ldx #$6051
L6203
	ldb #$36
L6205
	clra
L6206
	sta ,X+
L6208
	decb
L6209
	bne L6206
L620B
	ldx #$60D9
L620E
	ldb #$51
L6210
	sta ,X+
L6212
	decb
L6213
	bne L6210
L6215
	clr $60D8
L6218
	clr $612B
L621B
	clr $612A
L621E
	ldy #$6087
L6222
	clrb
L6223
	ldx #$6000
L6226
	lda B,X
L6228
	lbne L6233
L622C
	stb ,Y+
L622E
	inc $60D8
L6231
	bra L62A9
L6233
	sta $6132
L6236
	stb $612C
L6239
	ldx #$6452
L623C
	lda B,X
L623E
	sta $612D
L6241
	ldb $612C
L6244
	ldx #$64A3
L6247
	lda B,X
L6249
	sta $612E
L624C
	ldx #$64F4
L624F
	lda B,X
L6251
	sta $612F
L6254
	lda $6132
L6257
	deca
L6258
	asla
L6259
	ldx #$6440
L625C
	ldd A,X
L625E
	sta $6130
L6261
	stb $6131
L6264
	ldb $612D
L6267
	aslb
L6268
	ldx #$6051
L626B
	lda $6130
L626E
	ora B,X
L6270
	sta B,X
L6272
	incb
L6273
	lda $6131
L6276
	ora B,X
L6278
	sta B,X
L627A
	ldb $612E
L627D
	aslb
L627E
	ldx #$6063
L6281
	lda $6130
L6284
	ora B,X
L6286
	sta B,X
L6288
	incb
L6289
	lda $6131
L628C
	ora B,X
L628E
	sta B,X
L6290
	ldb $612F
L6293
	aslb
L6294
	ldx #$6075
L6297
	lda $6130
L629A
	ora B,X
L629C
	sta B,X
L629E
	incb
L629F
	lda $6131
L62A2
	ora B,X
L62A4
	sta B,X
L62A6
	ldb $612C
L62A9
	incb
L62AA
	cmpb #$51
L62AC
	lbcs L6223
L62B0
	lda $612B
L62B3
	fcb $10,$2B
L62B5
	fcb $01
L62B6
	bita #$B1
L62B8
	neg [16,U]
L62BB
	bcc L62BE
L62BD
	fcb $78
L62BE
	ldx #$6087
L62C1
	lda $612B
L62C4
	lda A,X
L62C6
	sta $612C
L62C9
	ldb $612C
L62CC
	ldx #$6452
L62CF
	lda B,X
L62D1
	sta $612D
L62D4
	ldx #$64A3
L62D7
	lda B,X
L62D9
	sta $612E
L62DC
	ldx #$64F4
L62DF
	lda B,X
L62E1
	sta $612F
L62E4
	ldb $612C
L62E7
	ldx #$6000
L62EA
	lda B,X
L62EC
	beq L6353
L62EE
	deca
L62EF
	asla
L62F0
	ldx #$6440
L62F3
	ldd A,X
L62F5
	sta $6130
L62F8
	stb $6131
L62FB
	lda $6130
L62FE
	coma
L62FF
	sta $6130
L6302
	lda $6131
L6305
	coma
L6306
	sta $6131
L6309
	ldb $612D
L630C
	aslb
L630D
	ldx #$6051
L6310
	lda $6130
L6313
	anda B,X
L6315
	sta B,X
L6317
	incb
L6318
	lda $6131
L631B
	anda B,X
L631D
	sta B,X
L631F
	ldb $612E
L6322
	aslb
L6323
	ldx #$6063
L6326
	lda $6130
L6329
	anda B,X
L632B
	sta B,X
L632D
	incb
L632E
	lda $6131
L6331
	anda B,X
L6333
	sta B,X
L6335
	ldb $612F
L6338
	aslb
L6339
	ldx #$6075
L633C
	lda $6130
L633F
	anda B,X
L6341
	sta B,X
L6343
	incb
L6344
	lda $6131
L6347
	anda B,X
L6349
	sta B,X
L634B
	ldb $612C
L634E
	ldx #$6000
L6351
	clr B,X
L6353
	ldx #$60D9
L6356
	lda $612B
L6359
	ldb A,X
L635B
	incb
L635C
	cmpb #$0A
L635E
	bcs L6369
L6360
	clrb
L6361
	stb A,X
L6363
	dec $612B
L6366
	lbra L62B0
L6369
	stb A,X
L636B
	pshs A,B
L636D
	tfr B,A
L636F
	deca
L6370
	asla
L6371
	ldx #$6440
L6374
	ldd A,X
L6376
	sta $6130
L6379
	stb $6131
L637C
	puls A,B
L637E
	ldb $612D
L6381
	aslb
L6382
	ldx #$6051
L6385
	lda $6130
L6388
	anda B,X
L638A
	lbne L6433
L638E
	incb
L638F
	lda $6131
L6392
	anda B,X
L6394
	lbne L6433
L6398
	ldb $612E
L639B
	aslb
L639C
	ldx #$6063
L639F
	lda $6130
L63A2
	anda B,X
L63A4
	lbne L6433
L63A8
	incb
L63A9
	lda $6131
L63AC
	anda B,X
L63AE
	lbne L6433
L63B2
	ldb $612F
L63B5
	aslb
L63B6
	ldx #$6075
L63B9
	lda $6130
L63BC
	anda B,X
L63BE
	lbne L6433
L63C2
	incb
L63C3
	lda $6131
L63C6
	anda B,X
L63C8
	lbne L6433
L63CC
	lda $612B
L63CF
	ldx #$60D9
L63D2
	ldb A,X
L63D4
	lda $612C
L63D7
	ldx #$6000
L63DA
	stb A,X
L63DC
	tfr B,A
L63DE
	deca
L63DF
	asla
L63E0
	ldx #$6440
L63E3
	ldd A,X
L63E5
	sta $6130
L63E8
	stb $6131
L63EB
	ldb $612D
L63EE
	aslb
L63EF
	ldx #$6051
L63F2
	lda $6130
L63F5
	ora B,X
L63F7
	sta B,X
L63F9
	incb
L63FA
	lda $6131
L63FD
	ora B,X
L63FF
	sta B,X
L6401
	ldb $612E
L6404
	aslb
L6405
	ldx #$6063
L6408
	lda $6130
L640B
	ora B,X
L640D
	sta B,X
L640F
	incb
L6410
	lda $6131
L6413
	ora B,X
L6415
	sta B,X
L6417
	ldb $612F
L641A
	aslb
L641B
	ldx #$6075
L641E
	lda $6130
L6421
	ora B,X
L6423
	sta B,X
L6425
	incb
L6426
	lda $6131
L6429
	ora B,X
L642B
	sta B,X
L642D
	inc $612B
L6430
	lbra L62B0
L6433
	lbra L62B0
L6436
	lda #$01
L6438
	sta $612A
L643B
	rts
L643C
	clr $612A
L643F
	rts
L6440
	neg <$02
L6442
	neg <$04
L6444
	neg <$08
L6446
	neg <$10
L6448
	neg <$20
L644A
	neg <$40
L644C
	neg <$80
L644E
	fcb $01
L644F
	neg <$02
L6451
	neg <$00
L6453
	neg <$00
L6455
	neg <$00
L6457
	neg <$00
L6459
	neg <$00
L645B
	fcb $01
L645C
	fcb $01
L645D
	fcb $01
L645E
	fcb $01
L645F
	fcb $01
L6460
	fcb $01
L6461
	fcb $01
L6462
	fcb $01
L6463
	fcb $01
L6464
	fcb $02
L6465
	fcb $02
L6466
	fcb $02
L6467
	fcb $02
L6468
	fcb $02
L6469
	fcb $02
L646A
	fcb $02
L646B
	fcb $02
L646C
	fcb $02
L646D
	com <$03
L646F
	com <$03
L6471
	com <$03
L6473
	com <$03
L6475
	com <$04
L6477
	lsr <$04
L6479
	lsr <$04
L647B
	lsr <$04
L647D
	lsr <$04
L647F
	fcb $05
L6480
	fcb $05
L6481
	fcb $05
L6482
	fcb $05
L6483
	fcb $05
L6484
	fcb $05
L6485
	fcb $05
L6486
	fcb $05
L6487
	fcb $05
L6488
	ror <$06
L648A
	ror <$06
L648C
	ror <$06
L648E
	ror <$06
L6490
	ror <$07
L6492
	asr <$07
L6494
	asr <$07
L6496
	asr <$07
L6498
	asr <$07
L649A
	asl <$08
L649C
	asl <$08
L649E
	asl <$08
L64A0
	asl <$08
L64A2
	asl <$00
L64A4
	fcb $01
L64A5
	fcb $02
L64A6
	com <$04
L64A8
	fcb $05
L64A9
	ror <$07
L64AB
	asl <$00
L64AD
	fcb $01
L64AE
	fcb $02
L64AF
	com <$04
L64B1
	fcb $05
L64B2
	ror <$07
L64B4
	asl <$00
L64B6
	fcb $01
L64B7
	fcb $02
L64B8
	com <$04
L64BA
	fcb $05
L64BB
	ror <$07
L64BD
	asl <$00
L64BF
	fcb $01
L64C0
	fcb $02
L64C1
	com <$04
L64C3
	fcb $05
L64C4
	ror <$07
L64C6
	asl <$00
L64C8
	fcb $01
L64C9
	fcb $02
L64CA
	com <$04
L64CC
	fcb $05
L64CD
	ror <$07
L64CF
	asl <$00
L64D1
	fcb $01
L64D2
	fcb $02
L64D3
	com <$04
L64D5
	fcb $05
L64D6
	ror <$07
L64D8
	asl <$00
L64DA
	fcb $01
L64DB
	fcb $02
L64DC
	com <$04
L64DE
	fcb $05
L64DF
	ror <$07
L64E1
	asl <$00
L64E3
	fcb $01
L64E4
	fcb $02
L64E5
	com <$04
L64E7
	fcb $05
L64E8
	ror <$07
L64EA
	asl <$00
L64EC
	fcb $01
L64ED
	fcb $02
L64EE
	com <$04
L64F0
	fcb $05
L64F1
	ror <$07
L64F3
	asl <$00
L64F5
	neg <$00
L64F7
	fcb $01
L64F8
	fcb $01
L64F9
	fcb $01
L64FA
	fcb $02
L64FB
	fcb $02
L64FC
	fcb $02
L64FD
	neg <$00
L64FF
	neg <$01
L6501
	fcb $01
L6502
	fcb $01
L6503
	fcb $02
L6504
	fcb $02
L6505
	fcb $02
L6506
	neg <$00
L6508
	neg <$01
L650A
	fcb $01
L650B
	fcb $01
L650C
	fcb $02
L650D
	fcb $02
L650E
	fcb $02
L650F
	com <$03
L6511
	com <$04
L6513
	lsr <$04
L6515
	fcb $05
L6516
	fcb $05
L6517
	fcb $05
L6518
	com <$03
L651A
	com <$04
L651C
	lsr <$04
L651E
	fcb $05
L651F
	fcb $05
L6520
	fcb $05
L6521
	com <$03
L6523
	com <$04
L6525
	lsr <$04
L6527
	fcb $05
L6528
	fcb $05
L6529
	fcb $05
L652A
	ror <$06
L652C
	ror <$07
L652E
	asr <$07
L6530
	asl <$08
L6532
	asl <$06
L6534
	ror <$06
L6536
	asr <$07
L6538
	asr <$08
L653A
	asl <$08
L653C
	ror <$06
L653E
	ror <$07
L6540
	asr <$07
L6542
	asl <$08
L6544
	fcb $08

	end	$6200
