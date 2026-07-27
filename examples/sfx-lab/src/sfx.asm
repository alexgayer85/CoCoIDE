***********************************************************************
* CoCoIDE SFX player — auto-generated (re-export from SFX Lab)
* IMPORTANT: working storage is fcb/fdb (in the .BIN). Do not use rmb
* after includebin — DECB load would omit those bytes.
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
* PlaySfx — A = id  (same algorithm as host simulate_playsfx_levels)
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
                lda     6,u
                sta     SfxVol
                lda     7,u
                sta     SfxVolEnd
                * vperiod = max(1, min(255,len)/max(1,|dv|))
                lda     6,u
                suba    7,u
                bpl     ps_abs
                nega
ps_abs          tsta
                bne     ps_dv
                lda     #1
ps_dv           tfr     a,b
                lda     SfxLen
                bne     ps_lhi
                lda     SfxLen+1
                bra     ps_div
ps_lhi          lda     #255
ps_div          pshs    b
                clrb
ps_divl         cmpa    ,s
                blo     ps_divd
                suba    ,s
                incb
                bne     ps_divl
ps_divd         tstb
                bne     ps_divok
                incb
ps_divok        stb     SfxVPeriod
                stb     SfxVCnt
                puls    a
                lda     ,u
                clrb
                tfr     d,x
                leax    SfxTables,x
                stx     SfxTab
                clr     SfxPhase
                ldd     #$ACE1
                std     SfxLfsr
                lda     $FF23
                ora     #$08
                sta     $FF23
                ldd     SfxLen
                lbeq    ps_quiet

ps_loop
                dec     SfxVCnt
                bne     ps_samp
                lda     SfxVPeriod
                sta     SfxVCnt
                lda     SfxVol
                cmpa    SfxVolEnd
                beq     ps_samp
                blo     ps_vup
                dec     SfxVol
                bra     ps_samp
ps_vup          inc     SfxVol
ps_samp
                lda     SfxFlags
                bita    #1
                bne     ps_nz
                ldx     SfxTab
                lda     SfxPhase
                lda     a,x
                bra     ps_dac
ps_nz           ldd     SfxLfsr
                bne     ps_n1
                ldd     #$ACE1
ps_n1           eora    SfxLfsr+1
                lsra
                rorb
                eora    SfxLfsr
                std     SfxLfsr
                lda     SfxFlags
                bita    #2
                bne     ps_wh
                lda     SfxLfsr+1
                anda    #63
                bra     ps_dac
ps_wh           lda     SfxLfsr
                anda    #63
                ldb     SfxLfsr+1
                andb    #63
                pshs    b
                suba    ,s+
                bpl     ps_w1
                nega
ps_w1           adda    #10
                cmpa    #63
                bls     ps_dac
                lda     #63
ps_dac          ldb     SfxVol
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
                bpl     ps_pb0
                lda     $FF22
                ora     #$02
                bra     ps_pb1
ps_pb0          lda     $FF22
                anda    #$FD
ps_pb1          sta     $FF22
                lda     SfxPhase
                adda    SfxPitch
                sta     SfxPhase
                ldb     #28
ps_del          decb
                bne     ps_del
                lda     SfxPitch
                cmpa    SfxPend
                beq     ps_next
                blo     ps_pin
                deca
                bra     ps_pst
ps_pin          inca
ps_pst          sta     SfxPitch
ps_next         ldd     SfxLen
                subd    #1
                std     SfxLen
                lbne    ps_loop
ps_quiet        lda     #$80
                sta     $FF20
ps_done         andcc   #$AF
                puls    cc,a,b,x,y,u
                rts

***********************************************************************
* Working storage MUST be real data bytes inside the DECB image
SfxFlags        fcb     0
SfxPitch        fcb     0
SfxPend         fcb     0
SfxVol          fcb     0
SfxVolEnd       fcb     0
SfxVPeriod      fcb     1
SfxVCnt         fcb     1
SfxPhase        fcb     0
SfxLen          fdb     0
SfxTab          fdb     0
SfxLfsr         fdb     $ACE1

SfxCat
        fcb     0,$00,$30,$30,$09,$C4,$38,$38  * 0: blip (square)
        fcb     1,$00,$46,$0E,$11,$94,$34,$28  * 1: dive (saw)
        fcb     2,$03,$64,$16,$0A,$F0,$2A,$04  * 2: shoo (whoosh)
        fcb     3,$00,$30,$03,$1F,$40,$3A,$14  * 3: sink (saw)
        fcb     4,$01,$24,$0E,$0D,$AC,$32,$0C  * 4: splash (noise)

SfxTables
                includebin sfx_tables.bin

                end     START
