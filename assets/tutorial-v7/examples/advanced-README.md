# V7 advanced-task templates / 进阶任务模板

这些文件是教学起点，不是已运行并验证的材料计算结果。
所有 INCAR.template 须先复制到自己的新任务目录，补齐标为 REPLACE 的数值，检查后才改名为 INCAR。
必须自行提供真实 POSCAR、经收敛的 KPOINTS 和有许可的 POTCAR；不在本包分发 POTCAR。
示例通常针对非磁半导体/绝缘体；实际金属、磁性、U、SOC、带电体系不可无审查直接套用。
表面/缺陷模板的参考态、电子数与固定层由研究问题决定。

## 原生 NEB 与 VTST 的关键差别
neb-native/INCAR.template 使用原生优化器和有限 POTIM，五个中间结构对应 00 至 06 七个 POSCAR。
neb-vtst/optimizer-overlay.INCAR.template 仅限确认编译了相容 VTST 的 VASP：IBRION=3、POTIM=0、IOPT=7。
在普通 VASP 中抄 POTIM=0 会导致离子不动。不能仅写 LCLIMB / IOPT 就启用 VTST。
VTST 片段需替换原 INCAR 对应行，不能让冲突设置并存。先 LCLIMB=.FALSE. 预收敛，检查路径后再单独续算并开启。

## Phonopy 与内置有限位移
phonon-internal 是 VASP 自行位移、求输入晶胞 Gamma 振动的路线。
phonopy 的 INCAR-force 用于外部位移结构的静态力，禁止再优化位移结构。
workflow.txt.template 按 Phonopy 4.5 风格提供 phonopy-init / phonopy 命令，需匹配安装版本。
样例只列两个 vasprun.xml 路径，必须替换成实际全部位移，严格保持 phonopy_disp.yaml 顺序。

## 其他限制
AIMD 模板 LANGEVIN_GAMMA 有两个值，只适用于两种 POTCAR 类型；POTIM 单位 fs。
HSE 需规则 k 网格与自洽轨道，不能 ICHARG=11 固定 PBE 密度。
LOPTICS 为独立粒子响应，不等于激子光谱；LEPSILON 模板不适用于 HSE。
弹性模板仅针对 3D bulk；含真空模型的 GPa 依赖盒子高度。
所有示范阈值与网格都必须按目标性质收敛，而非复制即达论文精度。

核验日期：2026-09-19。完整论述与官方链接见 vasp-advanced-v7.html。
