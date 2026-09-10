// SPDX-License-Identifier: MIT
// Read-only diagnostic consumer of Apache-2.0 FallrimTools, pinned in the report.
// No GUI entry point, save writer, cleaner, deletion, or mutation API is called.
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import resaver.ProgressModel;
import resaver.ess.*;
import resaver.ess.papyrus.*;

public final class SavePapyrusInventory {
    static boolean relevant(Object value) {
        String name = String.valueOf(value).toLowerCase(Locale.ROOT);
        return name.contains("truehud") || name.contains("ski_config") || name.contains("quickloot");
    }
    static String hash(Path path) throws Exception {
        return HexFormat.of().withUpperCase().formatHex(
            MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path)));
    }
    static void variables(HasVariables value) {
        List<Variable> vars = value.getVariables();
        List<MemberDesc> desc = value.getDescriptors();
        System.out.printf("variables=%d descriptors=%d%n", vars.size(), desc.size());
        for (int i = 0; i < vars.size(); ++i)
            System.out.printf("  [%d] %s = %s%n", i, i < desc.size() ? desc.get(i) : "<NO_DESCRIPTOR>", describe(vars.get(i)));
    }
    static String describe(Variable value) {
        // This pinned upstream's Array.getElementType subtracts 7, not 10.
        // Avoid its incorrect pretty-printed element label; use parsed fields.
        if (value instanceof Variable.Array array) {
            ArrayInfo info = array.getArray();
            return array.getType() + " id=" + array.getArrayID() +
                (info == null ? " referent=null" : " length=" + info.getLength() + " arrayElementType=" + info.getType());
        }
        return value.toString();
    }
    public static void main(String[] args) throws Exception {
        if (!Boolean.getBoolean("java.awt.headless") || args.length != 2)
            throw new IllegalArgumentException("Requires -Djava.awt.headless=true and save.ess expectedSHA256");
        Path path = Path.of(args[0]).toRealPath();
        if (Files.size(path) > 256L * 1024 * 1024) throw new IllegalArgumentException("ESS exceeds 256 MiB limit");
        String before = hash(path);
        if (!before.equalsIgnoreCase(args[1])) throw new IllegalArgumentException("Unexpected ESS hash");
        System.out.println("inputSHA256=" + before);
        ESS save = ESS.readESS(path, new ModelBuilder(new ProgressModel())).ESS;
        Papyrus pap = save.getPapyrus();
        if (save.isBroken() || pap == null || pap.isBroken()) throw new IllegalStateException("Parser reports incomplete/broken input; no conclusions permitted");
        System.out.printf("scripts=%d instances=%d active=%d suspended1=%d suspended2=%d messages=%d%n",
            pap.getScripts().size(), pap.getScriptInstances().size(), pap.getActiveScripts().size(),
            pap.getSuspendedStacks1().size(), pap.getSuspendedStacks2().size(), pap.getFunctionMessages().size());
        for (Script script : pap.getScripts().values()) if (relevant(script.getName())) {
            System.out.printf("SCRIPT %s parent=%s members=%s%n", script.getName(), script.getType(), script.getExtendedMembers());
        }
        for (ScriptInstance inst : pap.getScriptInstances().values()) if (relevant(inst.getScriptName())) {
            System.out.printf("INSTANCE %s form=%s%n", inst, inst.getRefID());
            variables(inst);
        }
        for (ActiveScript active : pap.getActiveScripts().values()) {
            System.out.printf("ACTIVE %s instance=%s attached=%s frames=%d%n", active.getID(), active.getInstance(), active.getAttached(), active.getStackFrames().size());
            for (StackFrame frame : active.getStackFrames()) {
                System.out.printf(" FRAME %s owner=%s%n", frame.getFName(), frame.getOwner());
                if (relevant(frame.getScriptName()) || relevant(frame.getOwner())) variables(frame);
            }
        }
        for (SuspendedStack stack : pap.getSuspendedStacks().values()) {
            System.out.printf("SUSPENDED %s message=%s%n", stack.getID(), stack.getMessage());
            if (stack.getMessage() != null && relevant(stack.getMessage())) variables(stack.getMessage());
        }
        for (FunctionMessage msg : pap.getFunctionMessages()) {
            System.out.printf("MESSAGE %s message=%s%n", msg.getID(), msg.getMessage());
            if (msg.getMessage() != null && relevant(msg.getMessage())) variables(msg.getMessage());
        }
        if (!before.equals(hash(path))) throw new IllegalStateException("Input changed during inspection");
        System.out.println("complete=true inputUnchanged=true");
    }
}
