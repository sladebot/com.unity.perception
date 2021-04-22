using System.Collections.Generic;
using UnityEditor;
using UnityEngine.Perception.Content;
using MenuItem = UnityEditor.MenuItem;
using UnityEngine;
using static UnityEngine.Perception.Content.CharacterValidation;
using System.Linq;

public class CharacterToolingUI : EditorWindow
{
    private static string[] toolbarNames = null;
    private enum TestResults
    {
        Inconclusive,
        Pass,
        Fail,
        Running
    }

    private TestResults testResults = new TestResults();
    private CharacterTooling contentTests = new CharacterTooling();

    private GameObject selection = null;
    private int toolbarSelection = 0;
    private bool drawFaceRays = false;

    private void OnSelectionChange()
    {
        selection = Selection.activeGameObject;
    }

    private void OnInspectorUpdate()
    {
        Repaint();
        selection = Selection.activeGameObject;
    }

    [MenuItem("Window/Perception Character Tool")]
    static void Init()
    {
        toolbarNames = new string[] { "Keypoints", "Validation" };
        CharacterToolingUI window = (CharacterToolingUI)GetWindow(typeof(CharacterToolingUI));
        window.autoRepaintOnSceneChange = true;
        window.Show();
    }

    private void OnGUI()
    {
        if (selection != null && selection.GetType() == typeof(GameObject))
        {
            EditorGUILayout.TextField("Selected Asset : ", selection.name);

            GUILayout.BeginHorizontal();
            toolbarSelection = GUILayout.Toolbar(toolbarSelection, toolbarNames);
            GUILayout.EndHorizontal();

            switch (toolbarSelection)
            {
                case 0:
                    GUILayout.Label("Character Tools", EditorStyles.whiteLargeLabel);
                    var test = false;
                    var failedBones = new Dictionary<HumanBone, bool>();
                    var failedPose = new List<GameObject>();

                    drawFaceRays = GUILayout.Toggle(drawFaceRays, "Draw Face Rays");
                    GUILayout.Label(string.Format("Create Ears and Noise: {0}", test), EditorStyles.boldLabel);


                    if (GUILayout.Button("Create Nose and Ears", GUILayout.Width(160)))
                    {
                        testResults = TestResults.Running;

                        test = contentTests.CharacterCreateNose(selection, drawFaceRays);

                        if (test)
                            testResults = TestResults.Pass;
                        if (!test)
                            testResults = TestResults.Fail;
                    }

                    break;

                case 1:

                    GUILayout.Label("Character Validation", EditorStyles.whiteLargeLabel);
                    GUILayout.Label(string.Format("Validation for Character : {0}", testResults), EditorStyles.whiteLabel);

                    var animator = selection.GetComponentInChildren<Animator>();

                    if (animator != null)
                    {
                        GUILayout.Label(string.Format("Character is Human: {0}", animator.avatar.isHuman), EditorStyles.boldLabel);
                        GUILayout.Label(string.Format("Character is Valid: {0}", animator.avatar.isValid), EditorStyles.boldLabel);
                    }

                    if (GUILayout.Button("Validate Bones", GUILayout.Width(160)))
                    {
                        testResults = TestResults.Running;

                        test = contentTests.CharacterRequiredBones(selection, out failedBones);

                        if (failedBones.Count > 0)
                        {
                            for (int i = 0; i < RequiredBones.Length; i++)
                            {
                                for (int b = 0; b < failedBones.Count; b++)
                                {
                                    var bone = failedBones.ElementAt(i);
                                    var boneKey = bone.Key;
                                    var boneValue = bone.Value;

                                    if (RequiredBones[i] == boneKey.humanName)
                                    {
                                        GUILayout.Label(string.Format("Bone {0}: {1}", RequiredBones[i], "Missing"), EditorStyles.boldLabel);
                                    }
                                }
                            }
                        }
                        else if (failedBones.Count == 0)
                        {
                            GUILayout.Label(string.Format("Required Bones Present : {0}", TestResults.Pass), EditorStyles.whiteLabel);
                        }

                        if (test)
                            testResults = TestResults.Pass;
                        if (!test)
                            testResults = TestResults.Fail;
                    }

                    if (GUILayout.Button("Validate Pose Data", GUILayout.Width(160)))
                    {
                        testResults = TestResults.Running;

                        test = contentTests.CharacterPoseData(selection, out failedPose);

                        if (test)
                            testResults = TestResults.Pass;
                        if (!test)
                            testResults = TestResults.Fail;
                    }

                    break;
            }
        }
    }
}
