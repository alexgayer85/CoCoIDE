***********************************************************************
* Sea Battle ML — CoCoIDE hybrid example
* Text-screen dual boards · CoCo 1/2/3 (DECB LOADM)
*
* From BASIC (main.bas):
*   CLEAR200,&H3F00
*   LOADM"SEA":EXEC
*
* Left board  = your fleet (PS)
* Right board = radar / your shots (RD)
***********************************************************************

POLCAT  equ     $A000           ; ROM vector: key in A, 0 if none
SCRN    equ     $0400           ; 32x16 text
COLS    equ     32
ROWS    equ     16
DAC     equ     $FF20
PIA1CRA equ     $FF01
PIA1CRB equ     $FF03
PIA2CRB equ     $FF23

        org     $3F00

***********************************************************************
* Entry
***********************************************************************
START
        lbsr    SeedRnd
        lbsr    SoundInit
        lbsr    TitleScreen
        lbsr    InitGame
        lbsr    PlacePlayerFleet
        lbsr    PlaceEnemyFleet
        lbsr    BattleLoop
        lbsr    GameOver
        rts

***********************************************************************
* Init
***********************************************************************
InitGame
        ldx     #PS
        lbsr    Clear100
        ldx     #ES
        lbsr    Clear100
        ldx     #RD
        lbsr    Clear100
        ldx     #AK
        lbsr    Clear100
        ldx     #SL
        lda     #5
        sta     ,x+
        lda     #4
        sta     ,x+
        lda     #3
        sta     ,x+
        lda     #3
        sta     ,x+
        lda     #2
        sta     ,x+
        ldx     #SR
        lda     #5
        sta     ,x+
        lda     #4
        sta     ,x+
        lda     #3
        sta     ,x+
        lda     #3
        sta     ,x+
        lda     #2
        sta     ,x+
        lda     #17
        sta     PH
        sta     EH
        clr     Hunt
        clr     HR
        clr     HC
        rts

Clear100
        ldb     #100
c100l   clr     ,x+
        decb
        bne     c100l
        rts

***********************************************************************
* Title
***********************************************************************
TitleScreen
        lbsr    Cls
        leax    MTitle,pcr
        ldy     #SCRN+1*COLS+8
        lbsr    PutStr
        leax    MSub,pcr
        ldy     #SCRN+3*COLS+6
        lbsr    PutStr
        leax    MFleet,pcr
        ldy     #SCRN+5*COLS+7
        lbsr    PutStr
        leax    MVs,pcr
        ldy     #SCRN+6*COLS+8
        lbsr    PutStr
        leax    MDual,pcr
        ldy     #SCRN+8*COLS+2
        lbsr    PutStr
        leax    MStart,pcr
        ldy     #SCRN+14*COLS+2
        lbsr    PutStr
        lbsr    WaitEnter
        rts

***********************************************************************
* Placement
***********************************************************************
PlacePlayerFleet
        lbsr    Cls
        leax    MPlace,pcr
        ldy     #SCRN+2*COLS+2
        lbsr    PutStr
        leax    MAM,pcr
        ldy     #SCRN+4*COLS+2
        lbsr    PutStr
        leax    MChoice,pcr
        ldy     #SCRN+14*COLS+0
        lbsr    PutStr
        lbsr    ReadLine
        lda     LineBuf
        cmpa    #'M
        beq     pp_man
        cmpa    #'m
        beq     pp_man
        ; default / A → auto
pp_auto
        lbsr    Cls
        leax    MAutoY,pcr
        ldy     #SCRN+5*COLS+2
        lbsr    PutStr
        clra                    ; grid 0 = player
        lbsr    AutoPlaceFleet
        lbsr    DrawDual
        leax    MReady,pcr
        ldy     #SCRN+14*COLS+0
        lbsr    PutStr
        lbsr    WaitEnter
        rts

pp_man
        lda     #1
        sta     ShipId
pp_mloop
        lda     ShipId
        cmpa    #6
        lbhs    pp_mdone
pp_mtry
        lbsr    DrawDual
        leax    MPlace2,pcr
        ldy     #SCRN+13*COLS+0
        lbsr    PutStr
        lda     ShipId
        lbsr    PutShipName     ; at current Y after PutStr? rewrite line
        leax    MCoord,pcr
        ldy     #SCRN+14*COLS+0
        lbsr    PutStr
        lbsr    ReadLine
        lbsr    ParseCoord
        lda     GR
        beq     pp_mbad
        leax    MHV,pcr
        ldy     #SCRN+15*COLS+0
        lbsr    PutStr
        lbsr    ReadLine
        lda     #0
        sta     Horiz
        lda     LineBuf
        cmpa    #'H
        beq     pp_mh
        cmpa    #'h
        bne     pp_mv
pp_mh   lda     #1
        sta     Horiz
pp_mv
        lda     GR
        sta     TmpR
        lda     GC
        sta     TmpC
        clr     TmpG            ; player grid
        ldb     ShipId
        ldx     #SL-1
        abx
        ldb     ,x
        stb     TmpL
        lbsr    CanPlace
        lda     CP
        beq     pp_mnoroom
        lda     TmpG
        ldb     ShipId
        lbsr    PlaceShip
        inc     ShipId
        lbra    pp_mloop
pp_mbad
        leax    MBad,pcr
        ldy     #SCRN+12*COLS+0
        lbsr    PutStr
        lbsr    WaitEnter
        lbra    pp_mtry
pp_mnoroom
        leax    MNoRoom,pcr
        ldy     #SCRN+12*COLS+0
        lbsr    PutStr
        lbsr    WaitEnter
        lbra    pp_mtry
pp_mdone
        lbsr    DrawDual
        leax    MReady,pcr
        ldy     #SCRN+14*COLS+0
        lbsr    PutStr
        lbsr    WaitEnter
        rts

PlaceEnemyFleet
        lbsr    Cls
        leax    MAutoE,pcr
        ldy     #SCRN+5*COLS+2
        lbsr    PutStr
        lda     #1              ; enemy grid
        lbsr    AutoPlaceFleet
        rts

***********************************************************************
* Auto place fleet: A = grid (0 player / 1 enemy)
***********************************************************************
AutoPlaceFleet
        sta     PlaceGrid
        lda     #1
        sta     ShipId
ap_ship
        lda     ShipId
        cmpa    #6
        lbhs    ap_done
        clr     Tries
ap_try
        inc     Tries
        lda     Tries
        cmpa    #200
        bhi     ap_next         ; give up this ship (shouldn't happen)
        lbsr    Rand
        anda    #1
        sta     Horiz
        ldb     ShipId
        ldx     #SL-1
        abx
        ldb     ,x
        stb     TmpL
        lda     Horiz
        bne     ap_h
        ; vertical: r = 1..11-len, c = 1..10
        lda     #11
        suba    TmpL
        lbsr    RandN           ; 1..A
        sta     TmpR
        lda     #10
        lbsr    RandN
        sta     TmpC
        bra     ap_chk
ap_h    ; horizontal: r=1..10, c=1..11-len
        lda     #10
        lbsr    RandN
        sta     TmpR
        lda     #11
        suba    TmpL
        lbsr    RandN
        sta     TmpC
ap_chk
        lda     PlaceGrid
        sta     TmpG
        lbsr    CanPlace
        lda     CP
        beq     ap_try
        lda     PlaceGrid
        ldb     ShipId
        lbsr    PlaceShip
ap_next
        inc     ShipId
        bra     ap_ship
ap_done
        rts

***********************************************************************
* CanPlace: TmpG,TmpR,TmpC,TmpL,Horiz → CP=1 if ok
***********************************************************************
CanPlace
        lda     #1
        sta     CP
        clr     TmpI
cp_lp
        lda     TmpI
        cmpa    TmpL
        bhs     cp_ok
        lda     TmpR
        ldb     TmpC
        tst     Horiz
        beq     cp_v
        ; horizontal: c + i
        addb    TmpI
        bra     cp_b
cp_v    adda    TmpI
cp_b
        ; bounds 1..10
        tsta
        beq     cp_bad
        cmpa    #10
        bhi     cp_bad
        tstb
        beq     cp_bad
        cmpb    #10
        bhi     cp_bad
        sta     RR
        stb     CC
        lda     TmpG
        bne     cp_es
        ldx     #PS
        bra     cp_cell
cp_es   ldx     #ES
cp_cell
        lda     RR
        ldb     CC
        lbsr    CellAddr        ; X = &grid[r,c]
        lda     ,x
        bne     cp_bad
        inc     TmpI
        bra     cp_lp
cp_bad
        clr     CP
cp_ok
        rts

***********************************************************************
* PlaceShip: A=grid B=id  uses TmpR,TmpC,Horiz, length from SL(id)
***********************************************************************
PlaceShip
        sta     TmpG
        stb     ShipId
        ldx     #SL-1
        abx
        ldb     ,x
        stb     TmpL
        clr     TmpI
ps_lp
        lda     TmpI
        cmpa    TmpL
        bhs     ps_done
        lda     TmpR
        ldb     TmpC
        tst     Horiz
        beq     ps_v
        addb    TmpI
        bra     ps_b
ps_v    adda    TmpI
ps_b
        sta     RR
        stb     CC
        lda     TmpG
        bne     ps_es
        ldx     #PS
        bra     ps_w
ps_es   ldx     #ES
ps_w
        lda     RR
        ldb     CC
        lbsr    CellAddr
        lda     ShipId
        sta     ,x
        inc     TmpI
        bra     ps_lp
ps_done
        rts

***********************************************************************
* CellAddr: X=base, A=row(1-10), B=col(1-10) → X = base+(r-1)*10+(c-1)
***********************************************************************
CellAddr
        deca
        decb
        pshs    b
        ldb     #10
        mul                     ; D = A*10
        addb    ,s+
        abx
        rts

***********************************************************************
* Battle
***********************************************************************
BattleLoop
bl_top
        lda     EH
        beq     bl_done
        lda     PH
        beq     bl_done
        lbsr    PlayerFires
        lda     EH
        beq     bl_done
        lbsr    ComputerFires
        lda     PH
        beq     bl_done
        bra     bl_top
bl_done
        rts

PlayerFires
pf_again
        lbsr    DrawDual
        leax    MShot,pcr
        ldy     #SCRN+13*COLS+0
        lbsr    PutStr
        leax    MShot2,pcr
        ldy     #SCRN+14*COLS+0
        lbsr    PutStr
        lbsr    ReadLine
        lda     LineBuf
        cmpa    #'F
        lbeq    pf_fleet
        cmpa    #'f
        lbeq    pf_fleet
        lbsr    ParseCoord
        lda     GR
        beq     pf_bad
        lda     #1              ; enemy grid for ApplyShot
        ldb     GR
        stb     TmpR
        ldb     GC
        stb     TmpC
        lbsr    ApplyShot
        lbsr    DrawDual
        lda     HT
        cmpa    #2
        beq     pf_alr
        cmpa    #0
        beq     pf_miss
        cmpa    #3
        beq     pf_sunk
        ; hit
        leax    MHit,pcr
        ldy     #SCRN+15*COLS+0
        lbsr    PutStr
        lda     #1
        lbsr    Beep
        lbsr    PauseShort
        rts
pf_miss
        leax    MMiss,pcr
        ldy     #SCRN+15*COLS+0
        lbsr    PutStr
        lda     #0
        lbsr    Beep
        lbsr    PauseShort
        rts
pf_sunk
        leax    MSunk,pcr
        ldy     #SCRN+15*COLS+0
        lbsr    PutStr
        lda     SID
        lbsr    PutShipNameAtY
        lda     #2
        lbsr    Beep
        lbsr    PauseShort
        rts
pf_alr
        leax    MAlready,pcr
        ldy     #SCRN+15*COLS+0
        lbsr    PutStr
        lbsr    PauseShort
        lbra    pf_again
pf_bad
        leax    MBad,pcr
        ldy     #SCRN+15*COLS+0
        lbsr    PutStr
        lbsr    PauseShort
        lbra    pf_again
pf_fleet
        ; dual already shows fleet; just pause
        leax    MReady,pcr
        ldy     #SCRN+15*COLS+0
        lbsr    PutStr
        lbsr    WaitEnter
        lbra    pf_again

***********************************************************************
* ApplyShot: A=grid (0=player 1=enemy), TmpR,TmpC → HT,SID
* HT: 0 miss, 1 hit, 2 already, 3 sunk
***********************************************************************
ApplyShot
        sta     TmpG
        clr     HT
        clr     SID
        lda     TmpG
        bne     as_en
        ; --- shot on player (computer fires) ---
        ldx     #PS
        lda     TmpR
        ldb     TmpC
        lbsr    CellAddr
        lda     ,x
        cmpa    #6
        lbeq    as_alr
        cmpa    #7
        lbeq    as_alr
        tsta
        beq     as_pmiss
        cmpa    #5
        lbhi    as_done
        sta     SID
        lda     #7
        sta     ,x
        ldx     #AK
        lda     TmpR
        ldb     TmpC
        lbsr    CellAddr
        lda     #2
        sta     ,x
        dec     PH
        lda     #1
        sta     HT
        ; count remaining cells of SID on PS
        lbsr    CountShipPS
        lda     TmpCnt
        lbne    as_done
        lda     #3
        sta     HT
        lbra    as_done
as_pmiss
        lda     #6
        sta     ,x
        ldx     #AK
        lda     TmpR
        ldb     TmpC
        lbsr    CellAddr
        lda     #1
        sta     ,x
        clr     HT
        lbra    as_done
as_en
        ; --- shot on enemy ---
        ldx     #RD
        lda     TmpR
        ldb     TmpC
        lbsr    CellAddr
        lda     ,x
        bne     as_alr
        ldx     #ES
        lda     TmpR
        ldb     TmpC
        lbsr    CellAddr
        lda     ,x
        tsta
        beq     as_emiss
        cmpa    #5
        lbhi    as_done
        sta     SID
        lda     #7
        sta     ,x
        ldx     #RD
        lda     TmpR
        ldb     TmpC
        lbsr    CellAddr
        lda     #2
        sta     ,x
        ldx     #SR-1
        ldb     SID
        abx
        dec     ,x
        dec     EH
        lda     #1
        sta     HT
        lda     ,x
        lbne    as_done
        lda     #3
        sta     HT
        lbra    as_done
as_emiss
        ldx     #RD
        lda     TmpR
        ldb     TmpC
        lbsr    CellAddr
        lda     #1
        sta     ,x
        clr     HT
        lbra    as_done
as_alr
        lda     #2
        sta     HT
as_done
        rts

CountShipPS
        clr     TmpCnt
        lda     #1
        sta     RR
cs_r    lda     #1
        sta     CC
cs_c    ldx     #PS
        lda     RR
        ldb     CC
        lbsr    CellAddr
        lda     ,x
        cmpa    SID
        bne     cs_n
        inc     TmpCnt
cs_n    inc     CC
        lda     CC
        cmpa    #11
        blo     cs_c
        inc     RR
        lda     RR
        cmpa    #11
        blo     cs_r
        rts

ComputerFires
        lbsr    DrawDual
        leax    MComp,pcr
        ldy     #SCRN+13*COLS+0
        lbsr    PutStr
        lbsr    PauseShort
        lbsr    AiPickShot
        lda     #0
        ldb     AR
        stb     TmpR
        ldb     AC
        stb     TmpC
        lbsr    ApplyShot
        lbsr    DrawDual
        leax    MAt,pcr
        ldy     #SCRN+14*COLS+0
        lbsr    PutStr
        ; print coord
        lda     AR
        adda    #64             ; 'A'-1 + r → 'A' if r=1? 64+1=65 'A' yes if AR is 1-based
        lbsr    PutCharY
        lda     AC
        cmpa    #10
        beq     cf_10
        adda    #'0
        lbsr    PutCharY
        bra     cf_msg
cf_10   lda     #'1
        lbsr    PutCharY
        lda     #'0
        lbsr    PutCharY
cf_msg
        lda     HT
        beq     cf_miss
        cmpa    #3
        beq     cf_sunk
        leax    MCompHit,pcr
        ldy     #SCRN+15*COLS+0
        lbsr    PutStr
        lda     #1
        sta     Hunt
        lda     AR
        sta     HR
        lda     AC
        sta     HC
        lda     #1
        lbsr    Beep
        bra     cf_end
cf_miss
        leax    MCompMiss,pcr
        ldy     #SCRN+15*COLS+0
        lbsr    PutStr
        lda     #0
        lbsr    Beep
        bra     cf_end
cf_sunk
        leax    MCompSink,pcr
        ldy     #SCRN+15*COLS+0
        lbsr    PutStr
        clr     Hunt
        lda     #2
        lbsr    Beep
cf_end
        lbsr    PauseShort
        rts

***********************************************************************
* AI pick → AR, AC
***********************************************************************
AiPickShot
        lda     Hunt
        lbeq    ai_rnd
        lda     #1
        sta     TmpI
ai_nb
        lda     TmpI
        cmpa    #5
        bhs     ai_rnd0
        lda     HR
        ldb     HC
        cmpa    #1
        bne     ai_d2
        ; wait use TmpI as dir 1-4
ai_d2
        lda     HR
        ldb     HC
        lda     TmpI
        cmpa    #1
        bne     ai_dir2
        lda     HR
        deca
        ldb     HC
        bra     ai_t
ai_dir2 cmpa    #2
        bne     ai_dir3
        lda     HR
        inca
        ldb     HC
        bra     ai_t
ai_dir3 cmpa    #3
        bne     ai_dir4
        lda     HR
        ldb     HC
        decb
        bra     ai_t
ai_dir4 lda     HR
        ldb     HC
        incb
ai_t
        tsta
        beq     ai_nx
        cmpa    #10
        bhi     ai_nx
        tstb
        beq     ai_nx
        cmpb    #10
        bhi     ai_nx
        sta     RR
        stb     CC
        ldx     #AK
        lbsr    CellAddr
        lda     ,x
        bne     ai_nx
        lda     RR
        sta     AR
        lda     CC
        sta     AC
        rts
ai_nx
        inc     TmpI
        bra     ai_nb
ai_rnd0
        clr     Hunt
ai_rnd
        clr     Tries
ai_lp
        inc     Tries
        lda     Tries
        cmpa    #200
        bhi     ai_scan
        lda     #10
        lbsr    RandN
        sta     AR
        lda     #10
        lbsr    RandN
        sta     AC
        ldx     #AK
        lda     AR
        ldb     AC
        lbsr    CellAddr
        lda     ,x
        bne     ai_lp
        rts
ai_scan
        lda     #1
        sta     AR
ais_r   lda     #1
        sta     AC
ais_c   ldx     #AK
        lda     AR
        ldb     AC
        lbsr    CellAddr
        lda     ,x
        beq     ais_ok
        inc     AC
        lda     AC
        cmpa    #11
        blo     ais_c
        inc     AR
        lda     AR
        cmpa    #11
        blo     ais_r
        ; fallback
        lda     #1
        sta     AR
        sta     AC
ais_ok
        rts

***********************************************************************
* Game over
***********************************************************************
GameOver
        lbsr    DrawDual
        leax    MOver,pcr
        ldy     #SCRN+13*COLS+8
        lbsr    PutStr
        lda     EH
        bne     go_lose
        leax    MWin,pcr
        ldy     #SCRN+14*COLS+10
        lbsr    PutStr
        lda     #2
        lbsr    Beep
        bra     go_wait
go_lose
        leax    MLose,pcr
        ldy     #SCRN+14*COLS+10
        lbsr    PutStr
        lda     #0
        lbsr    Beep
go_wait
        leax    MStart,pcr
        ldy     #SCRN+15*COLS+2
        lbsr    PutStr
        lbsr    WaitEnter
        rts

***********************************************************************
* Draw dual boards
* Left col 0-10: fleet fleet   Right col 16-26: radar
***********************************************************************
DrawDual
        lbsr    Cls
        leax    MHdrL,pcr
        ldy     #SCRN+0*COLS+1
        lbsr    PutStr
        leax    MHdrR,pcr
        ldy     #SCRN+0*COLS+17
        lbsr    PutStr
        leax    MCols,pcr
        ldy     #SCRN+1*COLS+1
        lbsr    PutStr
        leax    MCols,pcr
        ldy     #SCRN+1*COLS+17
        lbsr    PutStr
        lda     #1
        sta     RR
dd_row
        ; row letter left
        lda     RR
        adda    #64             ; 'A' for 1
        ldy     #SCRN+2*COLS
        ; Y = SCRN + (RR+1)*32
        pshs    a
        lda     RR
        inca                    ; screen row = RR+1 (rows 2..)
        ldb     #COLS
        mul
        ldy     #SCRN
        leay    d,y
        puls    a
        lbsr    PutCharY
        ; left cells
        lda     #1
        sta     CC
dd_lc
        ldx     #PS
        lda     RR
        ldb     CC
        lbsr    CellAddr
        lda     ,x
        lbsr    GlyphFleet
        lbsr    PutCharY
        inc     CC
        lda     CC
        cmpa    #11
        blo     dd_lc
        ; gap then letter right
        leay    5,y             ; move toward col 16 (we wrote 1+10=11 chars from col0)
        ; Actually after letter+10 cells Y is at col 11. Need col 16: +5
        lda     RR
        adda    #64
        lbsr    PutCharY
        lda     #1
        sta     CC
dd_rc
        ldx     #RD
        lda     RR
        ldb     CC
        lbsr    CellAddr
        lda     ,x
        lbsr    GlyphRadar
        lbsr    PutCharY
        inc     CC
        lda     CC
        cmpa    #11
        blo     dd_rc
        inc     RR
        lda     RR
        cmpa    #11
        blo     dd_row
        ; status line
        leax    MStat,pcr
        ldy     #SCRN+13*COLS+0
        ; don't overwrite battle prompts always — put scores on row 12
        ldy     #SCRN+12*COLS+0
        lbsr    PutStr
        lda     EH
        lbsr    PutNumY
        leax    MStat2,pcr
        lbsr    PutStrY
        lda     PH
        lbsr    PutNumY
        rts

GlyphFleet
        ; A = cell → glyph ascii
        tsta
        beq     gf_dot
        cmpa    #6
        beq     gf_o
        cmpa    #7
        beq     gf_star
        lda     #'#
        rts
gf_dot  lda     #'.
        rts
gf_o    lda     #'o
        rts
gf_star lda     #'*
        rts

GlyphRadar
        tsta
        beq     gr_dot
        cmpa    #1
        beq     gr_o
        lda     #'*
        rts
gr_dot  lda     #'.
        rts
gr_o    lda     #'o
        rts

***********************************************************************
* Screen helpers
***********************************************************************
Cls
        ldx     #SCRN
        lda     #$60            ; CoCo space
        ldy     #512
cls_l   sta     ,x+
        leay    -1,y
        bne     cls_l
        rts

* PutStr: X=ASCIIZ string (bit7 end or 0), Y=screen addr
PutStr
ps_l    lda     ,x+
        beq     ps_d
        lbsr    AscToScr
        sta     ,y+
        bra     ps_l
ps_d    rts

PutStrY
        ; X string, Y already set
        bra     PutStr

* PutCharY: A=ASCII, Y advances
PutCharY
        lbsr    AscToScr
        sta     ,y+
        rts

AscToScr
        cmpa    #$20
        bne     a1
        lda     #$60
        rts
a1      cmpa    #'A
        blo     a2
        cmpa    #'Z+1
        bhs     a_lo
        anda    #$1F
        rts
a_lo    cmpa    #'a
        blo     a2
        cmpa    #'z+1
        bhs     a2
        suba    #32
        anda    #$1F
        rts
a2      rts                     ; digits etc. pass through

* PutNumY: print 0-99 in A at Y
PutNumY
        clr     TmpH
pn_t    cmpa    #10
        blo     pn_o
        suba    #10
        inc     TmpH
        bra     pn_t
pn_o    pshs    a
        lda     TmpH
        adda    #'0
        lbsr    PutCharY
        puls    a
        adda    #'0
        lbsr    PutCharY
        rts

PutShipName
        ; print name for ShipId using Y (SCRN+13)
        ldy     #SCRN+13*COLS+12
PutShipNameAtY
        lda     SID
        beq     psn_use
        sta     ShipId
psn_use lda     ShipId
        cmpa    #1
        bne     psn2
        leax    N1,pcr
        bra     psn_go
psn2    cmpa    #2
        bne     psn3
        leax    N2,pcr
        bra     psn_go
psn3    cmpa    #3
        bne     psn4
        leax    N3,pcr
        bra     psn_go
psn4    cmpa    #4
        bne     psn5
        leax    N4,pcr
        bra     psn_go
psn5    leax    N5,pcr
psn_go  lbra    PutStr

***********************************************************************
* Keyboard
***********************************************************************
WaitEnter
we_d    jsr     [POLCAT]
        cmpa    #0
        bne     we_d            ; drain
we_w    jsr     [POLCAT]
        cmpa    #0
        beq     we_w
        cmpa    #13
        beq     we_ok
        cmpa    #3              ; break?
        beq     we_ok
        bra     we_w
we_ok   rts

ReadLine
        ldx     #LineBuf
        ldb     #0
        stb     LineLen
        ; clear buffer
        pshs    x
        lda     #12
rl_c    clr     ,x+
        deca
        bne     rl_c
        puls    x
rl_d    jsr     [POLCAT]
        tsta
        bne     rl_d
rl_l    jsr     [POLCAT]
        tsta
        beq     rl_l
        cmpa    #13
        beq     rl_done
        cmpa    #8
        beq     rl_bs
        cmpa    #$7F
        beq     rl_bs
        cmpa    #32
        blo     rl_l
        cmpa    #126
        bhi     rl_l
        ldb     LineLen
        cmpb    #10
        bhs     rl_l
        sta     ,x+
        inc     LineLen
        ; echo on bottom row
        pshs    a,x
        ldy     #SCRN+15*COLS
        ldb     LineLen
        decb
        leay    b,y
        puls    a,x
        lbsr    PutCharY
        bra     rl_l
rl_bs   ldb     LineLen
        beq     rl_l
        dec     LineLen
        leax    -1,x
        clr     ,x
        pshs    x
        ldy     #SCRN+15*COLS
        ldb     LineLen
        leay    b,y
        lda     #$60
        sta     ,y
        puls    x
        bra     rl_l
rl_done
        clr     ,x
        rts

ParseCoord
        ; LineBuf → GR,GC (0 if bad). Accept F already handled.
        clr     GR
        clr     GC
        ldx     #LineBuf
        ; skip spaces
pc_sp   lda     ,x+
        beq     pc_bad
        cmpa    #32
        beq     pc_sp
        ; letter
        cmpa    #'a
        blo     pc_up
        cmpa    #'z
        bhi     pc_up
        suba    #32
pc_up   cmpa    #'A
        blo     pc_bad
        cmpa    #'J
        bhi     pc_bad
        suba    #64             ; A→1
        sta     GR
        ; number
        lda     ,x+
        beq     pc_bad
        cmpa    #'0
        beq     pc_ten
        cmpa    #'1
        blo     pc_bad
        cmpa    #'9
        bhi     pc_bad
        suba    #'0
        sta     GC
        ; optional second digit for 10
        lda     ,x
        cmpa    #'0
        bne     pc_ok
        lda     GC
        cmpa    #1
        bne     pc_ok
        lda     #10
        sta     GC
        bra     pc_ok
pc_ten  lda     #10
        sta     GC
pc_ok   lda     GC
        beq     pc_bad
        cmpa    #10
        bhi     pc_bad
        rts
pc_bad  clr     GR
        clr     GC
        rts

***********************************************************************
* Random: LFSR seed; Rand → A; RandN: 1..A in A
***********************************************************************
SeedRnd
        lda     $0113           ; timer LSB if present
        bne     seed_ok
        lda     #$A5
seed_ok sta     Rnd
        rts

Rand
        lda     Rnd
        lsra
        bcc     rand_ok
        eora    #$B4
rand_ok sta     Rnd
        rts

RandN
        ; input A = N (1..N), output A = 1..N
        sta     TmpN
        beq     rn0
rn_l    lbsr    Rand
        tfr     a,b
        clra
        ; D = random 0..255; take mod N via subtract loop
        lda     TmpN
        ; use B mod A
        tstb
        ; simple: keep Rand until < N*floor
        lda     Rnd
rn_m    cmpa    TmpN
        blo     rn_ok
        suba    TmpN
        bra     rn_m
rn_ok   inca                    ; 1..N
        rts
rn0     lda     #1
        rts

PauseShort
        ldx     #$4000
ps_l2   leax    -1,x
        bne     ps_l2
        rts

***********************************************************************
* Sound
***********************************************************************
SoundInit
        lda     PIA1CRA
        ora     #$08
        sta     PIA1CRA
        lda     #$3C
        sta     PIA1CRB
        sta     PIA2CRB
        rts

* Beep: A=0 miss low, 1 hit, 2 sunk/high
Beep
        pshs    a,b,x
        tsta
        beq     bp_lo
        cmpa    #1
        beq     bp_md
        ldb     #40
        ldx     #20
        bra     bp_go
bp_lo   ldb     #12
        ldx     #50
        bra     bp_go
bp_md   ldb     #25
        ldx     #30
bp_go
        ; B = outer, X = delay
bp_o    lda     #$80
bp_i    sta     DAC
        eora    #$3F
        sta     DAC
        pshs    x
bp_d    leax    -1,x
        bne     bp_d
        puls    x
        deca
        bne     bp_i
        decb
        bne     bp_o
        puls    a,b,x
        rts

***********************************************************************
* Strings (ASCII, 0-terminated)
***********************************************************************
MTitle  fcn     "SEA BATTLE ML"
MSub    fcn     "NAVAL GRID COMBAT"
MFleet  fcn     "FLEET: 5 4 3 3 2"
MVs     fcn     "YOU VS COMPUTER"
MDual   fcn     "DUAL BOARD - TEXT MODE"
MStart  fcn     "PRESS ENTER"
MPlace  fcn     "PLACE YOUR FLEET"
MAM     fcn     "A=AUTO  M=MANUAL"
MChoice fcn     "CHOICE:"
MAutoY  fcn     "AUTO-DEPLOYING..."
MAutoE  fcn     "COMPUTER DEPLOYING..."
MReady  fcn     "PRESS ENTER"
MPlace2 fcn     "PLACE SHIP"
MCoord  fcn     "START (B3):"
MHV     fcn     "H=HORIZ V=VERT:"
MBad    fcn     "BAD COORD"
MNoRoom fcn     "NO ROOM"
MShot   fcn     "YOUR SHOT (A1-J0):"
MShot2  fcn     "OR F=PAUSE"
MHit    fcn     "HIT!"
MMiss   fcn     "MISS"
MSunk   fcn     "SUNK "
MAlready fcn    "ALREADY SHOT"
MComp   fcn     "COMPUTER FIRES..."
MAt     fcn     "AT "
MCompHit fcn    "COMPUTER HIT!"
MCompMiss fcn   "COMPUTER MISS"
MCompSink fcn   "SANK YOUR SHIP!"
MOver   fcn     "GAME OVER"
MWin    fcn     "YOU WIN!"
MLose   fcn     "YOU LOSE"
MHdrL   fcn     "YOUR FLEET"
MHdrR   fcn     "RADAR"
MCols   fcn     "1234567890"
MStat   fcn     "E:"
MStat2  fcn     " Y:"
N1      fcn     "CARRIER"
N2      fcn     "BATTLESHIP"
N3      fcn     "CRUISER"
N4      fcn     "SUBMARINE"
N5      fcn     "DESTROYER"

***********************************************************************
* Variables / grids (BSS after code)
***********************************************************************
PS      rmb     100
ES      rmb     100
RD      rmb     100
AK      rmb     100
SL      rmb     5
SR      rmb     5
PH      rmb     1
EH      rmb     1
Hunt    rmb     1
HR      rmb     1
HC      rmb     1
AR      rmb     1
AC      rmb     1
GR      rmb     1
GC      rmb     1
HT      rmb     1
SID     rmb     1
CP      rmb     1
Horiz   rmb     1
ShipId  rmb     1
PlaceGrid rmb   1
Tries   rmb     1
TmpG    rmb     1
TmpR    rmb     1
TmpC    rmb     1
TmpL    rmb     1
TmpI    rmb     1
TmpN    rmb     1
TmpH    rmb     1
TmpCnt  rmb     1
RR      rmb     1
CC      rmb     1
Rnd     rmb     1
LineLen rmb     1
LineBuf rmb     12

        end     START
