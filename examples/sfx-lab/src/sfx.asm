***********************************************************************
* CoCoIDE SFX player — auto-generated (re-export from SFX Lab)
* SoundInit / PlaySfx (A=id). Catalog: vol→vol_end envelope, pitch slide.
* Tables: sfx_tables.bin (1280 bytes). DAC $FF20, mux ORA #$08.
***********************************************************************

SFXCOUNT        equ     5

                org     $3F00

START
                lbsr    SoundInit
* Auto-play every effect once, then return to BASIC.
                clra
DemoAuto
                pshs    a
                lbsr    PlaySfx
                ldx     #$6000
da_w            leax    -1,x
                bne     da_w
                puls    a
                inca
                cmpa    #SFXCOUNT
                blo     DemoAuto
DemoDone
                rts

POLCAT          equ     $A000
WaitKey
                pshs    b,x
                andcc   #$EF
                ldx     #$4000
wk1             jsr     [POLCAT]
                anda    #$7F
                bne     wk2
                leax    -1,x
                bne     wk1
                clra
                puls    b,x
                rts
wk2             puls    b,x
                rts


SoundInit
                pshs    a
                orcc    #$50
                lda     $FF01
                ora     #$08
                sta     $FF01
                lda     $FF03
                ora     #$08
                sta     $FF03
                lda     $FF23
                ora     #$08
                sta     $FF23
                lda     $FF21
                anda    #$FB
                sta     $FF21
                lda     #$FC
                sta     $FF20
                lda     $FF21
                ora     #$04
                sta     $FF21
                lda     #$80
                sta     $FF20
                * PB1 out
                lda     $FF23
                anda    #$FB
                sta     $FF23
                lda     $FF22
                ora     #$02
                sta     $FF22
                lda     $FF23
                ora     #$04
                sta     $FF23
                andcc   #$AF
                puls    a
                rts

***********************************************************************
PlaySfx
                pshs    cc,a,b,x,y,u
                orcc    #$50
                cmpa    #SFXCOUNT
                lbhs    ps_done
                ldb     #8
                mul
                ldu     #SfxCat
                leau    d,u
                lda     1,u
                sta     SfxFlags
                lda     2,u
                sta     SfxPitch
                lda     3,u
                sta     SfxPend
                lda     4,u
                ldb     5,u
                std     SfxLen
                std     SfxLen0         ; original length for envelope
                lda     6,u
                sta     SfxVol
                lda     7,u
                sta     SfxVolEnd
                * period = max(1, min(255,len) / max(1,|dv|))
                lda     6,u
                suba    7,u
                bpl     ps_vd
                nega
ps_vd           tsta
                bne     ps_vs
                inca
ps_vs           tfr     a,b             ; B = |dv|
                lda     SfxLen
                bne     ps_vhi
                lda     SfxLen+1
                bra     ps_vdiv
ps_vhi          lda     #255
ps_vdiv         * A / B → period (8-bit)
                pshs    b
                clrb
ps_vq           cmpa    ,s
                blo     ps_vqd
                suba    ,s
                incb
                bne     ps_vq
ps_vqd          tstb
                bne     ps_vpok
                incb
ps_vpok         stb     SfxVPeriod
                stb     SfxVCnt
                puls    b
                lda     ,u
                clrb
                tfr     d,x
                leax    SfxTables,x
                stx     SfxTab
                clr     SfxPhase
                lda     $FF23
                ora     #$08
                sta     $FF23
                ldd     SfxLen
                lbeq    ps_quiet

ps_loop
                * volume step toward vol_end every SfxVPeriod samples
                dec     SfxVCnt
                bne     ps_vok
                lda     SfxVPeriod
                sta     SfxVCnt
                lda     SfxVol
                cmpa    SfxVolEnd
                beq     ps_vok
                blo     ps_vup
                dec     SfxVol
                bra     ps_vok
ps_vup          inc     SfxVol
ps_vok
                lda     SfxFlags
                bita    #$01
                bne     ps_noise
                ldx     SfxTab
                lda     SfxPhase
                lda     a,x
                bra     ps_scale
ps_noise
                ldd     SfxLfsr
                bne     ps_n1
                ldd     #$ACE1
ps_n1           eora    SfxLfsr+1
                lsra
                rorb
                eora    SfxLfsr
                std     SfxLfsr
                lda     SfxFlags
                bita    #$02
                bne     ps_whoosh
                lda     SfxLfsr+1
                anda    #63
                bra     ps_scale
ps_whoosh
                lda     SfxLfsr
                anda    #63
                ldb     SfxLfsr+1
                andb    #63
                stb     ,-s
                suba    ,s+
                bpl     ps_w1
                nega
ps_w1           adda    #10
                cmpa    #63
                bls     ps_scale
                lda     #63
ps_scale
                ldb     SfxVol
                mul
                lsra
                rorb
                lsra
                rorb
                lsra
                rorb
                lsra
                rorb
                lsra
                rorb
                lsra
                rorb
                tfr     b,a
                lsla
                lsla
                anda    #$FC
                sta     $FF20
                tsta
                bpl     ps_p0
                lda     $FF22
                ora     #$02
                bra     ps_p1
ps_p0           lda     $FF22
                anda    #$FD
ps_p1           sta     $FF22
                lda     SfxPhase
                adda    SfxPitch
                sta     SfxPhase
                ldb     #28
ps_d1           decb
                bne     ps_d1
                lda     SfxPitch
                cmpa    SfxPend
                beq     ps_len
                blo     ps_inc
                deca
                bra     ps_pst
ps_inc          inca
ps_pst          sta     SfxPitch
ps_len
                ldd     SfxLen
                subd    #1
                std     SfxLen
                lbne    ps_loop

ps_quiet
                lda     #$80
                sta     $FF20
ps_done
                andcc   #$AF
                puls    cc,a,b,x,y,u
                rts

SfxCat
        fcb     0,$00,$30,$30,$09,$C4,$38,$38  * 0: blip (square)
        fcb     1,$01,$24,$0E,$0D,$AC,$32,$0C  * 1: splash (noise)
        fcb     2,$00,$46,$0E,$11,$94,$34,$28  * 2: dive (saw)
        fcb     3,$03,$64,$16,$0A,$F0,$2A,$04  * 3: shoo (whoosh)
        fcb     4,$00,$30,$03,$1F,$40,$3A,$14  * 4: sink (saw)

SfxTables
                includebin sfx_tables.bin

SfxFlags        rmb     1
SfxPitch        rmb     1
SfxPend         rmb     1
SfxVol          rmb     1
SfxVolEnd       rmb     1
SfxVPeriod      rmb     1
SfxVCnt         rmb     1
SfxLen          rmb     2
SfxLen0         rmb     2
SfxPhase        rmb     1
SfxTab          rmb     2
SfxLfsr         fdb     $ACE1

                end     START
