using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

internal static class TranslatorBootstrap
{
    [STAThread]
    private static int Main()
    {
        string root = AppDomain.CurrentDomain.BaseDirectory;
        string runtimeExe = Path.Combine(root, "translator_runtime", "translator_app.exe");

        if (!File.Exists(runtimeExe))
        {
            MessageBox.Show(
                "找不到运行文件：" + runtimeExe,
                "划词翻译助手",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            );
            return 1;
        }

        string modelPath = Path.Combine(root, "Interpreter-Qwen3-1.7B.Q4_K_M.gguf");
        ProcessStartInfo startInfo = new ProcessStartInfo
        {
            FileName = runtimeExe,
            WorkingDirectory = root,
            UseShellExecute = false
        };

        if (File.Exists(modelPath))
        {
            startInfo.EnvironmentVariables["TRANSLATOR_MODEL_PATH"] = modelPath;
        }

        Process.Start(startInfo);
        return 0;
    }
}
