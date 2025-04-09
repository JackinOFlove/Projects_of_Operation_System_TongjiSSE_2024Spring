(function (window) {
    // 定义内存块、指令序列和缺页统计次数
    const document = window.document;
    let memory = [];
    let instruction = [];
    let numMissingPage = 0;

    // 获取页面元素
    const startButton = document.getElementById("Start_button");
    const clearButton = document.getElementById("Clear_button");
    const pageMissingCount = document.getElementById("Numbers_of_Missing_Page");
    const pageFaultRate = document.getElementById("Page_Fault_Rate");

    // 获取页面上三个参数的文本，并且转化为整数类型
    const numMemoryBlock = parseInt(document.getElementById("Number_of_Memory_Blocks").textContent);
    const numTotalInstruction = parseInt(document.getElementById("Number_of_Total_Instructions").textContent);
    const numInstructionPerPage = parseInt(document.getElementById("Number_of_Instructions_Per_Page").textContent);

    // 执行指令函数
    function executeInstructions() {
        const chooseAlgorithm = document.querySelector("input:checked").value;
        if (chooseAlgorithm === "FIFO") {
            fifoSimulation();
        } else {
            lruSimulation();
        }
    }

    // 判断是否缺页函数
    function judgeAvailable(instruction) {
        const page = Math.floor(instruction / numInstructionPerPage);
        for (let i = 0; i < memory.length; i++) {
            if (page === memory[i]) {
                return true;
            }
        }
        return false;
    }

    // FIFO算法的实现函数
    function fifoSimulation() {
        let fifoBlock = 0;

        for (let index = 0; index < instruction.length; index++) {
            const curInstruction = instruction[index];
            let removePage = -1;
            const currentPage = Math.floor(curInstruction / numInstructionPerPage);
            const instructionAvailable = judgeAvailable(curInstruction);

            if (!instructionAvailable) {
                // 设置缺页相关的参数
                numMissingPage++;
                pageMissingCount.textContent = numMissingPage;
                pageFaultRate.textContent = (numMissingPage / numTotalInstruction).toFixed(4);

                // 记录被移除页面页号和更新当前页面
                removePage = memory[fifoBlock % 4];
                memory[fifoBlock % 4] = currentPage;
                fifoBlock++;
            }

            // 将新的一行添加入结果显示表格中
            addInstructionsToTable(index, instructionAvailable, (fifoBlock - 1) % 4 + 1, removePage);
        }
    }

    // LRU算法的实现函数
    function lruSimulation() {
        // 访问顺序数组，越靠后越近访问
        let orderSequence = [0, 1, 2, 3];

        for (let index = 0; index < instruction.length; index++) {
            const curInstruction = instruction[index];
            let removePage = -1;
            const currentPage = Math.floor(curInstruction / numInstructionPerPage);
            const instructionAvailable = judgeAvailable(curInstruction);

            if (!instructionAvailable) {
                // 设置缺页相关的参数
                numMissingPage++;
                pageMissingCount.textContent = numMissingPage;
                pageFaultRate.textContent = (numMissingPage / numTotalInstruction).toFixed(4);

                // 记录被移除页面页号和更新当前页面
                removePage = memory[orderSequence[0]];
                memory[orderSequence[0]] = currentPage;
            }

            // 记录当前使用页面的所在内存块
            const lruBlock = memory.indexOf(currentPage);
            // 从指令序列中删去当前块号
            orderSequence.splice(orderSequence.indexOf(lruBlock), 1);
            // 将当前块号重新加入队尾(即最大的下标，最近使用)
            orderSequence.push(lruBlock);

            // 将新的一行添加入结果显示表格中
            addInstructionsToTable(index, instructionAvailable, lruBlock + 1, removePage);
        }
    }

    // 生成指令序列的函数
    function generateInstructions() {
        let index = 0;
        let preInstruction = -1;
        // 在0-319中随机生成一条指令
        let curInstruction = Math.floor(Math.random() * numTotalInstruction);
        // 将这一条指令放在指令序列的第一个
        instruction[0] = curInstruction;

        // 循环生成剩下的指令序列
        while (index < numTotalInstruction - 1) {
            preInstruction = curInstruction;

            // 50%的指令是顺序执行的
            if (index % 2 === 0 && curInstruction < numTotalInstruction - 1) {
                curInstruction++;
            }
            // 25%的指令是均匀分布在后地址的
            else if (index % 4 === 1 && curInstruction < numTotalInstruction - 2) {
                curInstruction = Math.floor(Math.random() * (numTotalInstruction - curInstruction - 2)) + curInstruction + 2;
            }
            // 25%的指令是均匀分布在前地址的
            else if (index % 4 === 3 && curInstruction > 0) {
                curInstruction = Math.floor(Math.random() * curInstruction);
            }
            // 如果两次生成的指令同一条，则随机再生成一条指令
            else {
                while (preInstruction === curInstruction) {
                    curInstruction = Math.floor(Math.random() * numTotalInstruction);
                }
            }

            // 将生成的指令加到指令序列中
            instruction[++index] = curInstruction;
        }
    }

    // 更新并显示表格内容的函数
    function addInstructionsToTable(index, instructionAvailable, block, removePage) {
        const curInstruction = instruction[index];
        const showTable = document.getElementById("showTable");

        // 每一条指令都插入新建的一行中
        const newRow = showTable.insertRow();

        // 添加行内容并应用淡入动画
        newRow.style.animation = 'fadeIn 0.5s ease-in';

        // 每一行的第1个单元格：序号
        newRow.insertCell(0).innerHTML = index + 1;
        // 每一行的第2个单元格：指令编号
        newRow.insertCell(1).innerHTML = "NO. " + curInstruction;

        // 每一行的第3、4、5、6个单元格：存放页面的页号或者是空的
        for (let i = 0; i < 4; i++) {
            newRow.insertCell(i + 2).innerHTML = memory[i] === undefined ? "Empty" : memory[i];
        }

        // 每一行的第7、8个单元格，判断是否缺页和载入、移出情况
        if (!instructionAvailable) {
            // 如果缺页，显示缺页情况和载入块号、移出页号
            const pageFaultCell = newRow.insertCell(6);
            pageFaultCell.innerHTML = "Yes";
            pageFaultCell.style.color = "red";

            newRow.insertCell(7).innerHTML = block;

            if (removePage === -1 || removePage === undefined) {
                newRow.insertCell(8).innerHTML = "- - -";
            } else {
                newRow.insertCell(8).innerHTML = removePage;
            }
        } else {
            // 如果不缺页，显示No
            newRow.insertCell(6).innerHTML = "No";
            newRow.insertCell(7).innerHTML = "- - -";
            newRow.insertCell(8).innerHTML = "- - -";
        }

        // 自动滚动到最新行
        showTable.parentNode.scrollTop = showTable.parentNode.scrollHeight;
    }

    // 清除函数，重置信息
    function clear() {
        // 重置三个全局变量
        memory = new Array(numMemoryBlock);
        instruction = new Array(numTotalInstruction);
        numMissingPage = 0;

        // 删除目前存在的表格信息
        const showTable = document.getElementById("showTable");
        while (showTable.rows.length > 1) {
            showTable.deleteRow(1);
        }

        // 将调页结果设为NULL
        pageMissingCount.textContent = "NULL";
        pageFaultRate.textContent = "NULL";
    }

    // 开始函数，开始执行
    function start() {
        // 显示加载中状态
        startButton.classList.add('loading');
        startButton.disabled = true;
        clearButton.disabled = true;

        // 使用setTimeout让UI有时间更新
        setTimeout(function () {
            // 清除已有信息、生成指令序列、执行指令
            clear();
            generateInstructions();
            executeInstructions();

            // 恢复按钮状态
            startButton.classList.remove('loading');
            startButton.disabled = false;
            clearButton.disabled = false;
        }, 100);
    }

    // 绑定事件触发类型
    startButton.addEventListener('click', start);
    clearButton.addEventListener('click', clear);
})(window);