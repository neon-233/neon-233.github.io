# 纪算 V6：VASP 学习文件

这些文件是中文教程的配套教学示例，未在本次网页开发中运行 VASP。
正式教程请从 tutorial-v6.html 开始，并阅读各文件对应章节。

## 使用前必须确认

1. 使用单位合法获得许可的 VASP 程序和 PAW 数据；压缩包不含程序、POTCAR 或真实计算结果。
2. 按 POSCAR 元素顺序准备对应 POTCAR，记录数据集版本、TITEL、ENMAX 和本地 SHA-256。
3. 硅入门输入仅针对指定原胞与 PBE 设置。所有截断能、k 网格和阈值均需检验。
4. .template 表示需要修改的模板；出现大写占位词、尖括号说明或缺少结构文件时，不可原样运行。
5. 各任务独立建目录，保留先前输入输出；按照章节复制 CHGCAR、CONTCAR 或 WAVECAR。
6. 电子收敛、离子停止、数值精度与物理可信度需要分别检查。不要把模板运行结束等同于科研结论。
7. 高级任务还要求正确的结构、边界条件、磁态和方法选择。原生 VASP 与 VTST 不能混用参数。
8. 任何作业脚本中的队列、模块名、核数与程序路径都由实际集群规定，先向管理员确认。

文件采用 UTF-8 与 LF 换行。VASP 输入格式请遵循对应官方文档；中文说明不必复制到 INCAR。

## 文件索引
- si-scf/POSCAR — 教学输入；需自备授权 Si POTCAR，并核查 ENMAX 与收敛。
- si-scf/KPOINTS — 教学输入；需自备授权 Si POTCAR，并核查 ENMAX 与收敛。
- si-scf/INCAR — 教学输入；需自备授权 Si POTCAR，并核查 ENMAX 与收敛。
- si-scf/README.txt — 教学输入；需自备授权 Si POTCAR，并核查 ENMAX 与收敛。
- si-relax/INCAR — 配合相同硅 POSCAR/POTCAR 与已收敛网格；520 eV 必须核查体积优化精度。
- si-relax/README.txt — 优化不是已经完成的计算；请核验最终力与应力。
- si-static/INCAR — 从已核验收敛的 si-relax/CONTCAR 复制 POSCAR，势文件保持一致。
- si-static/KPOINTS — 从已核验收敛的 si-relax/CONTCAR 复制 POSCAR，势文件保持一致。
- si-static/README.txt — 下载包不虚构优化后结构，需要先完成自己的优化。
- prepare_convergence.py — 只生成目录与输入，不提交、不运行 VASP；会拒绝覆盖目标目录。
- submit.slurm.template — 必须替换队列和模块占位符，并按计算中心说明调整启动器。
- calculation-record.md.template — 每次实际计算后填写，不使用假想结果。
- si-dos/INCAR — 需要同一硅原胞已收敛的 POSCAR、POTCAR 和 CHGCAR；数值为待检验教学起点。
- si-dos/KPOINTS — 需要同一硅原胞已收敛的 POSCAR、POTCAR 和 CHGCAR；数值为待检验教学起点。
- si-bands/INCAR — 需要同一硅原胞已收敛的 POSCAR、POTCAR 和 CHGCAR；数值为待检验教学起点。
- si-bands/KPOINTS — 需要同一硅原胞已收敛的 POSCAR、POTCAR 和 CHGCAR；数值为待检验教学起点。
- si-dos/README.txt — 避免将 ICHARG=1 误认为固定电荷密度。
- si-bands/README.txt — 路径仅对应本教程原胞，不能直接移植到其他晶胞。
- fe-fm/POSCAR — 自备授权 Fe PAW-PBE 势，重新做 Fe 的收敛测试。2.87 Å 为固定教学几何。
- fe-fm/KPOINTS — 自备授权 Fe PAW-PBE 势，重新做 Fe 的收敛测试。2.87 Å 为固定教学几何。
- fe-fm/INCAR — 自备授权 Fe PAW-PBE 势，重新做 Fe 的收敛测试。2.87 Å 为固定教学几何。
- fe-afm/INCAR — 复制 fe-fm 的相同结构、网格和势；从头初始化，不读已有磁化密度。
- fe-afm/README.txt — 对照结果需要实际求解，反向初态未必保持到最终。
- dft-u/INCAR.template — 明确未就绪：需要 Ni2O2 磁性结构、相容网格、Ni O 势文件，以及有依据的 Ueff 和截断能。
- dft-u/README.txt — 避免臆定磁性晶胞或“通用 U”。
- si-soc/INCAR — 必须使用 vasp_ncl；配套复制非磁性硅静态结构、势、CHGCAR 和均匀网格。
- si-soc/README.txt — 三分量磁矩和程序类型必须同时正确。
- si-charge/INCAR — 配套相同已核验结构、势和收敛网格；LAECHG 输出后还需检验细 FFT 网格。
- si-charge/README.txt — 不把 Bader 分区电荷直接当作整数氧化态。
- surface/INCAR.template — 需补 slab 结构、许可 POTCAR、已收敛 k 网格、ENCUT 和 DIPOL；示例不含磁性或电荷态。
- defect/INCAR.template — 需补真实超胞、k 点、赝势、电子数与自旋方案；不含自动形成能或通用电荷校正。
- phonon-internal/INCAR.template — 仅限已优化结构的输入晶胞 Γ 点模式；需对力精度和位移收敛，不是完整声子色散。
- phonopy/INCAR-force.template — 用于每个外部位移超胞，禁止离子优化；需统一参数、补齐结构与赝势。
- phonopy/workflow.txt.template — 按官方 Phonopy 4.5 命令体系编写；实际位移数量和路径需替换，未提供或执行真实计算。
- elastic/INCAR.template — 只适用已充分优化的三维体相；需收敛应力精度，不能直接用于含真空二维模量。
- neb-native/INCAR.template — 固定晶胞，五个中间结构；需七套端点/中间 POSCAR。原生优化器使用有限 POTIM。
- neb-vtst/optimizer-overlay.INCAR.template — 非完整 INCAR；仅替换已验证 VTST 程序的对应行。普通 VASP 禁止使用 POTIM=0 片段。
- aimd-nvt/INCAR.template — 两种原子类型的短程试算；需修改元素摩擦数组、时间步和生产采样长度，不提供真实轨迹。
- vdw/pbe-d3bj-overlay.INCAR.template — 仅为补充片段，需合并到完整且验证过的 PBE 输入；不能与其他色散方案盲目叠加。
- hse06/INCAR.template — 从头开始的非磁半导体静态计算；需要规则 k 网格及已收敛 ENCUT，不能使用固定 PBE 电荷密度捷径。
- optics/INCAR.template — 三维非磁绝缘体的自洽频率响应；NBANDS、ENCUT 与 k 网格均需收敛，不含激子。
- dielectric/INCAR.template — 电子钳位离子介电响应与 Born 电荷；不含完整离子贡献，不适用于 HSE 的 LEPSILON 计算。
- advanced-README.md — 先读此说明；明确原生 NEB / VTST、Phonopy 版本与所有模板的适用限制。
- report/calculation-report.md — 空白研究记录，含模型、方法、收敛、运行环境与证据边界；可按具体任务填写。
- report/practice-checklist.md — 可填写的报告框架；所有结果留空，不包含模拟数据或自动评分。
- tools/inspect_vasp_run.py — 只读提取最后能量与力、停止消息和文件哈希；不自动认证收敛。Python标准库即可运行。
