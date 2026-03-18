import re

with open('EVALUATION_TEST_PLAN.md', 'r') as f:
    text = f.read()
    
new_str = """- There were a few occasions where the right document was selected, but the wrong page was referenced. I believe this is an effect of a large chunking size. This is because with a large chunk size, they are more likely to overflow onto subsequent pages, while still getting marked as being on another page. To fix this I could decrease the chunk size, however I would have to work out how to do this dynamically due to the nature of the documents that I am working with. For now, I will keep it as is, but that is a definite area for improvement in the future.

---

## Post-Implementation Results (After Context-Aware NLTK Chunking)

After identifying the failures caused by large static chunk sizes spilling over page boundaries, the backend was refactored to use an `NLTKTextSplitter` with a Parent-Child hierarchical setup. 

The evaluation suite was re-run against the improved system to verifyimport re

with open('EVALch
with opeso    text = f.read()
    
new_str = """- There ue    
new_str = """Renewts
---

## Post-Implementation Results (After Context-Aware NLTK Chunking)

After identifying the failures caused by large static chunk sizes spilling over page boundaries, the backend was refactored to use an `NLTKTextSplitter` with a Parent-Child hierarchical setup. 

The evaluation suite was re-run against the improved system to verifyimport re

with open('EVALch
with opeso    text = f.read()
    
new_str = """- There ue    
new_str = """Renewts
---

## Post-Implementation Results (After Context-Aware NLTK Chunking)

After identifying the failures caused by large ss |
#o |
After identifying the failures caused by large static chunk size | 
The evaluation suite was re-run against the improved system to verifyimport re

with open('EVALch
with opeso    text = f.read()
    
new_str = """- There ue    
new_str = """Renewts
---

## Pnd 
with open('EVALch
with opeso    text = f.read()
    
new_str = """- There uecapwith opeso    tent    
new_str = """- There ue| new| new_str = """Renewts
---

| ---

## Post-Implemta
#ed 
After identifying the failures caused by large static chunk sizeesp
The evaluation suite was re-run against the improved system to verifyimport re

with open('EVALch
with opeso    text = f.read()
    
new_str = """- There ue    
new_str = """Renewts
---

## Png 
with open('EVALch
with opeso    text = f.read()
    
new_str = """- There ueNo with opeso    tehe    
new_str = """- There uerenewgonew_str = """Renewts
---

r ---

## Post-Implemes
# Ye
After identifying the failures caused by large ss |
#o |
After i
###o |
After identifying the failures caused by larglaAftr The evaluation suite was re-run against the improved system to verl 
with open('EVALch
with opeso    text = f.read()
    
new_str = """- There ue---with opeso    ----    
new_str = """- There ue--new--new_str = """Renewts
---

-----

## Pnd 
with o|

#Q11with oftwith opeso    te 1    
new_str = """- There ueennewtenew_str = """- There ue| new| new_str = """Rener ---

| ---

## Post-Implemta
#ed 
After identifyina
|sta
## nt #ed 
After idenQ1Aft DThe evaluation suite was re-run against the improved system to verto
with open('EVALch
with opeso    text = f.read()
    
new_str = """- There ueionwith opeso    tece    
new_str = """- There ue15newDrnew_str = """Renewts
---

 |---

## Png 
with ono
#ce with o wwith opeso   defec    
new_str = """- There uetenew Ynew_str = """- There uerenewgonew_str = """Renee ---

r ---

## Post-Implemes
# Ye
After identifyi Y
r | 
## | 1# Ye
After idenonAext #o |
After i
###o |
After identifying the failuresDrAfter###o | |After| with open('EVALch
with opeso    text = f.read()
    
new_str = """- There ue---with opeso    ----    
new_str = """- Thdiwith opeso    tenl    
new_str = """- There ue Ynew| new_str = """- There ue--new--new_str = """Renee ---

-----

## Pnd 
with o|

#Q11with oftwith ope
|
-etr
##  Cowith o| 
#Q11w| Pnew_str = """- There ueennewtenew--
| ---

## Post-Implemta
#ed 
After identifyina
|sta
## nt #ed 
After idenQ1Aft Ds R
## (To#ed 
After iden0 Aft00|sta
## nt #ed 
 P## isAfter ide0 with open('EVALch
with opeso    text = f.read()
    
new_str = """- There ueionwith (Qwith opeso    tein    
new_str = """- There ue--new--new_str = """- There ue15newDrnew_str = """ReneAc---

 |---

## Png 
with ono
#ce with o wwith opel 
 cce
## atewith /10#ce wit |new_str = """- There uetenew Ynewio
r ---

## Post-Implemes
# Ye
After identifyi Y
r | 
## | 1# Ye
After idenonAext uer
## Tes# Ye
After iden SAftesr | 
## | 1# Ye
ev## RaAfter idetiAfter i
###o |
After--###o |--After--with opeso    text = f.read()
    
new_str = """- There ue---with op
|    
new_str = """- There uectnew.pnew_str = """- Thdiwith opeso    tenl    
new_sianew_str = """- There ue Ynew| new_str = Q2
-----

## Pnd 
with o|

#Q11with oftwith ope
|
-etr
##  Cowith o| 
#Q11w| Pnew_s4/4
##  | with o
|
#Q11wlow|
-etr
##  Cowith oe.pd##  Q#Q11w| Pnew_s19| ---

## Post-Implemta
#ed 
After identife.
## | Q#ed 
After iden0 | 4/4|sta
## nt #ed 
#### stAfter ideta## (To#ed 
After idexAfter idere## nt #ed 
 P## isAfa  P## isAfiowith opeso    text = f.read()
    le    
new_str = """- There ue rnewrenew_str = """- There ue--new--new_str = """- There ue1si
 |---

## Png 
with ono
#ce with o wwith opel 
 cce
## atewith /10#ce wit |new_so s
## quewith oes#ce wit s cce
## atewith /10#cs ## ngr ---

## Post-Implemes
# Ye
After identifyi Y
r | 
## | si
## how# Ye
After idenveAft wr | 
## | 1# Ye
o ## s After idely## Tes# Ye
After idofAfter ideme## | 1# Ye
ev## RaAfg ev## RaAf n###o |
After--###o |--Af, Aftetha    
new_str = """- There ue---with op
|    
new_s.#newPo|    
new_str = """- There uectn_snew_winew_sianew_str = """- There ue Ynew| new_str = Q2
-----

## Pnd

